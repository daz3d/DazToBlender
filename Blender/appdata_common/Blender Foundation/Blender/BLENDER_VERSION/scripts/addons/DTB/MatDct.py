import os
import bpy
import pprint
from . import Global
import re

class MatDct:
    dct = {}
    bpart = [
    ["face", "1"],
    ["head", "1"],
    ["ears","1"],
    ["eyesocket","1"],
    ["lips","1"],
    ["torso","2"],
    ["legs","3"],
    ["toenails","3"],
    ["arms","4"],
    ["fingernails","4"],
    ["mouth","5"],
    ["teeth","5"],
    ["eyelashes","0"],
    ["irises","6"],
    ["sclera","6"],
    ["pupils","6"],
    ["irises","7"],
    ["sclera","7"],
    ["pupils","7"],
    ["cornea","8"],
    ["eyemoisture","8"],
    ["genitaria","9"],["anus","9"],["rectum","9"],
    ["labia","9"],["clitoris","9"],["vagina","9"],["glans","9"],["shaft","9"],["testicles","9"],
    ]
    imgs = [
    ["diff","diff","d"],
    ["diff", "MapD", "d"],
    ["Albedo", "mapd", "d"],
    ["Base", "TX", "d"],
    ["base_color", "basecolor", "d"],
    ["Base Color", "BaseColor", "d"],
    ["bump","bump","b"],
    ["bump","MapB","b"],
    ["bump", "mapb", "b"],
    ["bump", "mapb01", "b"],
    ["bump", "Height", "b"],
    ["bump", "bmp.", "b"],
    ["bump", "disp.", "b"],
    ["bump","MapB01","b"],
    ["specu","specc.","s"],
    ["specu", "spec.", "s"],
    ["specu", "MapS", "s"],
    ["specu", "Maps", "s"],
    ["sss","sss","z"],
    ["normal","nm","n"],
    ["rough","rough","r"],
    ["trans","tr","t"],
    ["eyelashes","eyelashes","t"],
    ["diff","D","d"],
    ["bump","B","b"],
    ["specu","S","s"],
    ["sss","sss","z"],
    ["normal","NM","n"],
    ["normal", "nml.", "n"],
    ["normal","Nm","n"],
    ["rough","R","r"],
    ["trans","TR","t"],
    ["trans","Tr","t"],
    ["Alpha","alpha","t"]
    ]
    evaluate = -1


    def getResult(self):
        return self.dct

    def getEvaluate(self):
        point = 0
        for i in range(len(self.bpart)):
            for j in range(1,len(self.imgs)):
                key = self.bpart[i][1]+self.imgs[j][2]
                if key in self.dct.keys():
                    point +=1
        return

    def makeDctFromShader(self):
        pass

    def makeDctFromBody(self):
        main_adr = ""
        for slot in Global.getBody().material_slots:
            mat = bpy.data.materials.get(slot.name)
            if mat is not None:
                for n in mat.node_tree.nodes:
                    if n.name=='Principled BSDF':
                        bcolor = n.inputs.get('Base Color')
                        if bcolor is not None:
                            for lk in bcolor.links:
                                if lk.from_node.name.startswith("Image Texture"):
                                    adr = lk.from_node.image.filepath
                                    sname = slot.name
                                    a = sname.rfind(".00")
                                    if a>2:
                                        sname = sname[0:a]
                                    for b in self.bpart:
                                        if (b[0].lower() in sname.lower()):
                                            bnum = b[1]
                                            if bnum == '6':
                                                bnum = '7'
                                            key = bnum + "d"
                                            self.add_dct(key,adr)
                                            if int(bnum)<5 and main_adr=="":
                                                main_adr = os.path.dirname(adr)
        if main_adr != "":
            self.search_directory(main_adr)

    def makeDctFromDirectory(self,adr):
        self.dct = {}
        self.search_directory(adr)

    def makeDctFromMtl(self):
        self.dct = {}
        self.makeDctFromBody()
        main_adr = ""
        hometown = Global.getHomeTown()
        if os.path.exists(hometown)==False:
            mtl = Global.getRootPath()+'DTB.mtl'
        else:
            mtl = hometown +"/FIG.mtl"
        if os.path.exists(mtl)==False:
            return
        list = []
        with open(mtl,errors = 'ignore', encoding='utf-8') as f:
            ls = f.readlines()
        for l in ls:
            l = l.strip()
            l = l.replace('"','')
            if len(l)>2:
                list.append(l.lower())
        directory_memo = ""
        for i in range(len(list)):
            s_line = list[i]
            if s_line.startswith("newmtl"):
                key = ""
                tr_key = ""
                name_key = ""
                for b in self.bpart:
                    if (b[0].lower() in s_line[7:].lower()) \
                    or ((b[0].lower()+"_") in s_line[7:].lower()) \
                    or (("_" + b[0].lower()) in s_line[7:].lower()):
                        if name_key=='':
                            name_key = s_line[7:].lower()
                        bnum = b[1]
                        if bnum=='6':
                            bnum = '7'
                        if key=='':
                            key = bnum+"d"
                        if tr_key=='':
                            tr_key = bnum+"t"
                        #bc_key = b[1] + "c"
                        break
                if key=="":
                    key = s_line[7:].lower()+"_d"
                    tr_key = s_line[7:].lower()+"_t"

                bc_key = s_line[7:].lower() + "_c"
                j = i + 1
                adr = ""
                tr_adr = ""
                bc_value =[]
                ac_value =1.0
                while j<len(list):
                    if list[j].startswith("newmtl"):
                        break
                    if list[j].startswith("map"):
                        a = list[j].find(" ")
                        if a>-1:
                            if list[j].startswith("map_kd"):
                                adr = list[j][a + 1:]
                                if os.path.exists(adr) == False:
                                    wk = os.path.dirname(adr)
                                    if (os.path.exists(wk) and os.path.isdir(wk) and directory_memo == ""):
                                        directory_memo = wk
                                    adr = ""
                            elif list[j].startswith("map_d"):
                                tr_adr = list[j][a + 1:]
                                if os.path.exists(tr_adr) == False:
                                    tr_adr = ""
                    elif list[j].startswith("kd ") and len(list[j])>=8:
                        s3 = list[j][3:].split()
                        for s1 in s3:
                            bc_value.append(float(s1))
                        bc_value.append(1.0)
                    elif list[j].startswith("d ") and len(list[j])>=3:
                        ac_value = float(list[j][2:])
                    j+=1
                if adr!="":
                    if main_adr=="" and ('_' in key) ==False:
                        main_adr = adr
                    self.add_dct(key,adr)
                self.add_dct(tr_key,tr_adr)
                if len(bc_value)==4:
                    if ac_value != 1.0:
                        bc_value[3] = ac_value
                    self.add_dct(bc_key,bc_value)
        main_adr = os.path.dirname(main_adr);
        if main_adr=="":
            main_adr =  directory_memo
        if main_adr!="":
            self.search_directory(main_adr)

    def add_dct(self,key,adr):
        if adr=="":
            return
        if (key in self.dct)==False:
            self.dct.setdefault(key,adr)
        elif ('_' in key) and len(key)>2:
            for i in range(1,10):
                a = key.rfind("_")
                key2 = key[:a]+".00"+str(i) + key[a:]
                if(key2 in self.dct.keys())==False:
                    self.dct.setdefault(key2,adr)
                    break

    def judge_kind(self,tech,stud,z,iscloth):
        if z == 0:
            if(tech in stud) or (tech.lower() in stud.lower()) or (tech.upper() in stud.upper()):
                return True
        else:
            if len(tech)==1:
                if iscloth:
                    return False
                else:
                    tech = tech.upper()
            kg = ['-','.','_']
            for k in kg:
                if ((tech+k) in stud) or ((k+tech) in stud):
                    return True
            if (len(tech) > 2 and tech[:1].isupper() and tech[1:].islower() and (tech in stud)):
                return True
        return False

    def search_directory(self,main_adr):
        mf_adr = [
            "C:\\Users\\Public\\Documents\\My DAZ 3D Library\\Runtime\\Textures\\DAZ\\Characters\\Genesis8\\FemaleBase",
            "C:\\Users\\Public\\Documents\\My DAZ 3D Library\\Runtime\\Textures\\DAZ\\Characters\\Genesis8\\MaleBase"]
        mf_mac_adr = [
            "/Users/Share/My DAZ 3D Library/Runtime/Textures/DAZ/Characters/Genesis8/FemaleBase",
            "/Users/Share/My DAZ 3D Library/Runtime/Textures/DAZ/Characters/Genesis8/MaleBase"]
        avec_adr = [main_adr, ""]
        if Global.getIsMan():
            if os.name == 'nt':
                avec_adr[1] = mf_adr[1]
            else:
                avec_adr[1] = mf_mac_adr[1]
        else:
            if os.name == 'nt':
                avec_adr[1] = mf_adr[0]
            else:
                avec_adr[1] = mf_mac_adr[0]
        if avec_adr[0] == avec_adr[1]:
            avec_adr[1] = "skip"
        for aidx in range(len(avec_adr)):
            if aidx > 0:
                self.imgs.append(["diff", "Eyes01", "d"])
            aadr = avec_adr[aidx]
            if os.path.exists(aadr) and os.path.isdir(aadr):
                list = os.listdir(path=aadr)
                for l in list:
                    L = l
                    l = l.lower()
                    twd = ["", ""]
                    for z in range(2):
                        for bb in self.bpart:
                            if bb[1] == '10':
                                break
                            b = bb[z]
                            if z == 0 and (b in l) or z > 0 and (("00" + b) in l):
                                if twd[0] == "":
                                    twd[0] = bb[1]
                                    break
                        for img in self.imgs:
                            ig = img[z]
                            if self.judge_kind(ig,L,z,False) or self.judge_kind(ig,l,z,False):
                                if twd[1] == "":
                                    twd[1] = img[2]
                                    break
                            if len(ig)==1 and z>0:
                                pat = "[a-z]" + ig.upper() + "\d"
                                rep = re.compile(pat)
                                result = rep.search(L)
                                if result:
                                    if twd[1] == "":
                                        twd[1] = img[2]
                                        break
                    if twd[0] != "" and twd[1] != "":
                        if twd[0] == '6':
                            twd[0] = '7'
                        wd = twd[0] + twd[1]
                        self.add_dct(wd,aadr+Global.getFileSp()+L)
        #pprint.pprint(self.dct)

    def cloth_dct_0(self,adr):
        c_dir = os.path.dirname(adr)
        c_name = os.path.splitext(os.path.basename(adr))[0]
        if not os.path.exists(c_dir):
            return None
        if c_name != "":
            for i in range(3):
                if i==0:
                    rtn = self.cloth_dct(c_name, c_dir,adr)
                    if rtn !=[]:
                        return rtn
                elif i==1:
                    for img in self.imgs:
                        if img[2]=='d':
                            for j in range(2):
                                if c_name.endswith(img[j]):
                                    myc_name = c_name[0:len(c_name)-len(img[j])]
                                    rtn = self.cloth_dct(myc_name, c_dir,adr)

                                    if rtn !=[]:
                                        return rtn
                else:
                    if len(c_name) >= 12:
                        c_name = c_name[:(len(c_name) // 2) - 2]
                    elif len(c_name) >= 8:
                        c_name = c_name[:3]
                    else:
                        c_name = c_name[:1]
                    return self.cloth_dct(c_name, c_dir,adr)
        return None

    def cloth_dct(self,cname,aadr,skip_adr):
        skip_adr = os.path.realpath(os.path.abspath(skip_adr))
        cloth_dct = []
        if os.path.exists(aadr) and os.path.isdir(aadr):
            list = os.listdir(path=aadr)
            for l in list:
                L = l
                l = l.lower()
                if L.startswith(cname)==False:
                    continue
                twd = [cname, ""]
                for z in range(2):
                    for img in self.imgs:
                        ig = img[z]
                        if self.judge_kind(ig, L, z,True) or self.judge_kind(ig, l, z,True):
                            if twd[1] == "":
                                twd[1] = img[2]
                                break
                if twd[0] != "" and twd[1] != "":
                    wd = twd[0] +"-" +  twd[1]
                    for cd in cloth_dct:
                        if cd[0]==wd:
                            wd = ""
                            break
                    if wd!="":
                        ans = aadr + Global.getFileSp() + L
                        ans = os.path.realpath(os.path.abspath(ans))
                        if skip_adr!=ans:
                            cloth_dct.append([wd,ans])
        return cloth_dct