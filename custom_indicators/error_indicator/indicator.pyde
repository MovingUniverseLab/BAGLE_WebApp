# Transformation angle
angle = 0

# Radius of circle
radius = 20

# Number of triangles
num_tri = 36

# Initial equilateral triangle side-length
l_side = 100

# (x, y) coordinates of initial equilateral triangle
# This is a equilateral triangle with lower-right vertex at (0, 0)
init_pt1 = [0, 0]
init_pt2 = [-l_side, 0]
init_pt3 = [-l_side/2, -l_side/2 * sqrt(3)]
init_pts = [init_pt1, init_pt2, init_pt3]

# Offset initial equilateral triangle for radius
for pt in init_pts:
    pt[0] -= radius/2 * sqrt(3)
    pt[1] -= radius/2

# Colors for page
clrs = {
    'bg_dark': '#2b3035',
    'sides_dark': ('#ff3333', '#ff0000', '#cc0000')
}

theme = 'dark'

##########################################
# Setup and Drawing
##########################################
def setup():
    size(250, 250)
    pixelDensity(2)
    
def draw():
    global angle
    
    background(clrs['bg_' + theme])
    strokeWeight(1)
    
    # Translate from top-left to better show drawing
    translate(width/2, height/2)
    
    # Transform triangle
    stroke_pts = []
    for pt in init_pts:
        x = pt[0] * cos(radians(angle)) + pt[1] * sin(radians(angle)) * cos(radians(angle))
        y = pt[1] * sin(radians(angle)) - pt[0] * cos(radians(angle)) * sin(radians(angle))
        
        stroke_pts.append((x, y))
    
    # Draw circle of shapes 
    for a in range(0, 360, 360/num_tri):
        pushMatrix()
        
        # Rotate drawing space
        rotate(radians(a))
            
        # Draw triangle
        num_strokes = len(stroke_pts)
        for i in range(num_strokes):
            idx1 = i
            idx2 = (i + 1) % num_strokes
    
            stroke(clrs['sides_' + theme][i])
            line(stroke_pts[idx1][0], stroke_pts[idx1][1], 
                 stroke_pts[idx2][0], stroke_pts[idx2][1])
            
        popMatrix()

    # This will save 360 frames
    saveFrame('frames_' + theme + '/img_####.png')
    
    angle += 4
    if angle >= 360:
        noLoop()
