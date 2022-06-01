
from collections import OrderedDict
from itertools import repeat
CYCLES = True
VRAY = not CYCLES

class values():
    average_y = 0
    x_last = 0
    margin_x = 400
    mat_name = ""
    margin_y = 40

def toNodeArrange(ntree):
    #bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    nodes_iterate(ntree)
    nodes_center(ntree)

def outputnode_search(ntree):
    outputnodes = []
    for node in ntree:
        if not node.outputs:
            for input in node.inputs:
                if input.is_linked:
                    outputnodes.append(node)
                    break
    if not outputnodes:
        return None
    return outputnodes

def nodes_iterate(ntree):
    nodeoutput = outputnode_search(ntree)
    if nodeoutput is None:
        return None
    a = []
    a.append([])
    for i in nodeoutput:
        a[0].append(i)
    level = 0
    while a[level]:
        a.append([])
        for node in a[level]:
            inputlist = [i for i in node.inputs if i.is_linked]
            if inputlist:
                for input in inputlist:
                    for nlinks in input.links:
                        node1 = nlinks.from_node
                        a[level + 1].append(node1)
        level += 1
    del a[level]
    level -= 1
    for x, nodes in enumerate(a):
        a[x] = list(OrderedDict(zip(a[x], repeat(None))))

    top = level 
    for row1 in range(top, 1, -1):
        for col1 in a[row1]:
            for row2 in range(row1-1, 0, -1):
                for col2 in a[row2]:
                    if col1 == col2:
                        a[row2].remove(col2)
                        break
    levelmax = level + 1
    level = 0
    values.x_last = 0

    while level < levelmax:
        values.average_y = 0
        nodes = [x for x in a[level]]
        nodes_arrange(nodes, level)
        level = level + 1
    return None

def nodes_arrange(nodelist, level):

    parents = []
    for node in nodelist:
        parents.append(node.parent)
        node.parent = None
    widthmax = max([x.dimensions.x for x in nodelist])
    xpos = values.x_last - (widthmax + values.margin_x) if level != 0 else 0
    values.x_last = xpos
    x = 0
    y = 0

    for node in nodelist:
        if node.hide:
            hidey = (node.dimensions.y / 2) - 8
            y = y - hidey
        else:
            hidey = 0
        node.location.y = y
        y = y - values.margin_y - 240 + hidey
        #y = y - values.margin_y - node.dimensions.y + hidey
        node.location.x = xpos
        
    y = y + values.margin_y
    center = (0 + y) / 2
    values.average_y = center - values.average_y

    for node in nodelist:
        node.location.y -= values.average_y

    for i, node in enumerate(nodelist):
        node.parent =  parents[i]

def nodes_center(ntree):

    bboxminx = []
    bboxmaxx = []
    bboxmaxy = []
    bboxminy = []

    for node in ntree:
        if not node.parent:
            bboxminx.append(node.location.x)
            bboxmaxx.append(node.location.x + node.dimensions.x)
            bboxmaxy.append(node.location.y)
            bboxminy.append(node.location.y - node.dimensions.y)

    bboxminx = min(bboxminx)
    bboxmaxx = max(bboxmaxx)
    bboxminy = min(bboxminy)
    bboxmaxy = max(bboxmaxy)
    center_x = (bboxminx + bboxmaxx) / 2
    center_y = (bboxminy + bboxmaxy) / 2
    x = 0
    y = 0

    for node in ntree:
        if not node.parent:
            node.location.x -= center_x
            node.location.y += -center_y
