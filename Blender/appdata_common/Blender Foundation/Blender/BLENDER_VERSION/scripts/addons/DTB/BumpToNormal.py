# this blender script will create a normal map from bump map
# reference: https://gist.github.com/Huud/63bacf5b8fe9b7b205ee42a786f922f0
#
# This conversion is very slow. So you better reuse the normal map you already has
import bpy
import os
import numpy as np


BLENDER_IMAGE_FORMAT = ['BMP', 'IRIS', 'PNG', 'JPEG', 'JPEG2000', 'TARGA', 'TARGA_RAW', 'CINEON', 'DPX', 'OPEN_EXR_MULTILAYER', 'OPEN_EXR', 'HDR', 'TIFF']

# a function that takes a vector - three numbers - and normalize it, i.e make it's length = 1
def normalizeRGB(vec):
    length = np.sqrt(vec[:,:,0]**2 + vec[:,:,1]**2 + vec[:,:,2]**2)
    vec[:,:,0] = vec[:,:,0] / length
    vec[:,:,1] = vec[:,:,1] / length
    vec[:,:,2] = vec[:,:,2] / length
    return vec

# src_image is a blender image object, not a path
# returned normal object is a ndarray
def heightMapToNormalMap(src_image):

    if src_image is None:
        return None
   
    rgba = np.asarray(src_image.pixels)
    rgba = rgba.reshape((src_image.size[0], src_image.size[1], 4))
    # print("rgba.shape:")
    # print(rgba.shape)

    # only use r channel here
    image = rgba[:,:,0]
    alpha = rgba[:,:,3]
    alpha = alpha.reshape((src_image.size[0], src_image.size[1], 1))
    
    # initialize the normal map, and the two tangents:
    normalMap = np.zeros((image.shape[0],image.shape[1],3))
    tan       = np.zeros((image.shape[0],image.shape[1],3))
    bitan     = np.zeros((image.shape[0],image.shape[1],3))

    
    # we get the normal of a pixel by the 4 pixels around it, sodefine the top, buttom, left and right pixels arrays,
    # which are just the input image shifted one pixel to the corrosponding direction. We do this by padding the image
    # and then 'cropping' the unneeded sides
    #
    # butaixianran:
    # I exchanged B and T, because the generated normal map is in wrong direction
    # After exchange B and T, I get the right result
    T = np.pad(image,1,mode='edge')[2:,1:-1]
    B = np.pad(image,1,mode='edge')[:-2,1:-1]
    L = np.pad(image,1,mode='edge')[1:-1,0:-2]
    R = np.pad(image,1,mode='edge')[1:-1,2:]
    
    # to get a good scale/intensity multiplier, i.e a number that let's the R and G channels occupy most of their available  
    # space between 0-1 without clipping, we will start with an overly strong multiplier - the smaller the the multiplier is, the
    # stronger it is -, to practically guarantee clipping then incrementally increase it until no clipping is happening
    scale = .05
    while True:
        
        #get the tangents of the surface, the normal is thier cross product
        tan[:,:,0],tan[:,:,1],tan[:,:,2]       = np.asarray([scale, 0 , R-L], dtype="object")
        bitan[:,:,0],bitan[:,:,1],bitan[:,:,2] = np.asarray([0, scale , B-T], dtype="object")
        normalMap = np.cross(tan,bitan)

        # normalize the normals to get their length to 1, they are called normals after all
        normalMap = normalizeRGB(normalMap)
        
        # increment the multiplier until the desired range of R and G is reached 
        if scale > 2: break
        if np.max(normalMap[:,:,0]) > 0.95  or np.max(normalMap[:,:,1]) > 0.95 \
        or np.min(normalMap[:,:,0]) < -0.95 or np.min(normalMap[:,:,1]) < -0.95:
            scale += .05
            continue
        else: 
            break
    
    # calculations were done for the channels to be in range -1 to 1 for the channels, however the image saving function
    # expects the range 0-1, so just divide these channels by 2 and add 0.5 to be in that range, we also flip the 
    # G channel to comply with the OpenGL normal map convention
    normalMap[:,:,0] = (normalMap[:,:,0]/2)+.5
    normalMap[:,:,1] = (0.5-(normalMap[:,:,1]/2))
    normalMap[:,:,2] = (normalMap[:,:,2]/2)+.5
    
    # normalizing does most of the job, but clip the remainder just in case 
    normalMap = np.clip(normalMap,0.0,1.0)
    
    # now, this normalMap only has rgb channel
    # so we need to add an alpha channel for it
    # create an alpha channel with all white
    # alpha = [1.0]*(src_image.size[0] * src_image.size[1])
    # np_alpha = np.asarray(alpha)
    # np_alpha = np_alpha.reshape((src_image.size[0], src_image.size[1], 1))

    #merge alpha into normalmap
    normal = np.concatenate((normalMap, alpha), axis=2)
    
    return normal


# normal path is the file path you want to save your normal map
# if ok, return True, else return False
# if normal file exist, it will rewrite it
# blender's image format: https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.file_format
# reuse: bool, if true, and file already exist, it will use it. If false, it will rewrite normal map
# max_size is the max width  or height, set to zero to ignore size
def bumpToNormal(bump_path, normal_path, normal_name, file_format, max_size):
    src_image = bpy.data.images.load(bump_path)

    if src_image is None:
        print("can not find bump file: " + bump_path)
        return False

    # resize
    # ignore size if max_size is 0
    if max_size > 0:
        width = src_image.size[0]
        height = src_image.size[1]
        max_length = height

        if width > height:
            max_length = width
        
        if max_length > max_size:
            resize_rate = max_size/max_length
            width = width * resize_rate
            height = height * resize_rate

            src_image.scale(width, height)

    # np_normal is a ndarray
    np_normal = heightMapToNormalMap(src_image)

    # create normalMap file
    normal_image = bpy.data.images.new(normal_name, width=src_image.size[0], height=src_image.size[1], is_data=True)
    
    normal_image.file_format = file_format
    
    normal_image.filepath = normal_path
    # set pixels
    normal_image.pixels = np_normal.ravel()
    # save image
    # image.save() will ignore any format setting, it always save as PNG
    # so, to use JPEG format, we need to use image.save_render(filepaht)
    render_format = bpy.context.scene.render.image_settings.file_format
    # set render's file format
    bpy.context.scene.render.image_settings.file_format = file_format
    normal_image.save_render(normal_path)
    #restore render's file format
    bpy.context.scene.render.image_settings.file_format = render_format

    return True


# convert bump_path to normal map path
# return normal_path, normal_name and ext
def getNormalPath(bump_path):
    if not os.path.isfile(bump_path):
        print("bump_path is not a file: " + bump_path)
        return ""

    dir = os.path.dirname(bump_path)
    # basename = filename.ext
    bumpBasename = os.path.basename(bump_path)
    # split  "/path/foo.bar" into: ["/path/foo", ".bar"], then remove "." from ext
    bumpFileName, ext = os.path.splitext(bumpBasename)
    ext = ext[1:]

    #now we need normal_path, normal_name, file_format
    normal_name = bumpFileName+"_normal"+"."+ext
    normal_path = dir + "/" + normal_name

    return normal_path, normal_name, ext

# this will create a normal map into the folder of bump map
# use the same file type as bump map
# and named it as: bumpFileName_normal
# reuse: bool, if true, and file already exist, it will use it. If false, it will rewrite normal map
# max_size is the max width or height, set to zero to ignore size
# return the new normal map's path
# if failed, return empty string
def bumpToNormalAuto(bump_path, max_size, reuse):
    if not os.path.isfile(bump_path):
        print("bump_path is not a file: " + bump_path)
        return ""

    normal_path, normal_name, ext = getNormalPath(bump_path)

    # blender's file format:
    # https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.file_format
    file_format = "PNG"
    ext = ext.upper()
    if ext == "JPG":
        file_format = "JPEG"
    elif ext == "TGA":
        file_format = "TARGA"
    elif ext in BLENDER_IMAGE_FORMAT:
        file_format = ext
    
    print("normal file format: "+ file_format)

    if reuse:
        # check if normal_path exist
        if os.path.isfile(normal_path):
            # reuse it
            return normal_path

    if bumpToNormal(bump_path, normal_path, normal_name, file_format, max_size):
        return normal_path
    else:
        return ""



    
    

