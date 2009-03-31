#!/usr/bin/env python
#
############################################################################
#
# MODULE:	r.fillnulls
# AUTHOR(S):	Markus Neteler <neteler itc it>
#               Updated to GRASS 5.7 by Michael Barton
#               Updated to GRASS 6.0 by Markus Neteler
#               Ring improvements by Hamish Bowman
#               Converted to Python by Glynn Clements
# PURPOSE:	fills NULL (no data areas) in raster maps
#               The script respects a user mask (MASK) if present.
#
# COPYRIGHT:	(C) 2001,2004-2005,2008 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################


#%Module
#% description: Fills no-data areas in raster maps using v.surf.rst splines interpolation
#% keywords: raster, elevation, interpolation
#%End
#%option
#% key: input
#% gisprompt: old,cell,raster
#% type: string
#% description: Raster map in which to fill nulls
#% required : yes
#%end
#%option
#% key: output
#% gisprompt: new,cell,raster
#% type: string
#% description: Output raster map with nulls filled by interpolation from surrounding values
#% required : yes
#%end
#%option
#% key: tension
#% type: double
#% description: Spline tension parameter
#% required : no
#% answer : 40.
#%end
#%option
#% key: smooth
#% type: double
#% description: Spline smoothing parameter
#% required : no
#% answer : 0.1
#%end

import sys
import os
import atexit
import grass

# what to do in case of user break:
def cleanup():
    #delete internal mask and any TMP files:
    rasts = [tmp1 + ext for ext in ['', '.buf', '_filled']]
    grass.run_command('g.remove', flags = 'f', rast = rasts)
    grass.run_command('g.remove', flags = 'f', vect = vecttmp)
    grass.run_command('g.remove', rast = 'MASK')
    if grass.find_file(usermask, mapset = mapset)['file']:
	grass.run_command('g.rename', rast = (usermask, 'MASK'))

def main():
    global vecttmp, tmp1, usermask, mapset

    input = options['input']
    output = options['output']
    tension = options['tension']
    smooth = options['smooth']

    #check if input file exists
    if not grass.find_file(input)['file']:
	grass.fatal("<%s> does not exist." % input)

    mapset = grass.gisenv()['MAPSET']
    unique = str(os.getpid())

    # check if a MASK is already present:
    usermask = "usermask_mask." + unique
    if grass.find_file('MASK', mapset = mapset)['file']:
	grass.message("A user raster mask (MASK) is present. Saving it...")
	grass.run_command('g.rename', rast = ('MASK',usermask))

    #make a mask of NULL cells
    tmp1 = "r_fillnulls_" + unique

    # idea: filter all NULLS and grow that area(s) by 3 pixel, then
    # interpolate from these surrounding 3 pixel edge

    grass.message("Locating and isolating NULL areas...")
    #creating 0/1 map:
    grass.mapcalc("$tmp1 = if(isnull($input),1,null())",
		  tmp1 = tmp1, input = input)

    #generate a ring:
    # the buffer is set to three times the map resolution so you get nominally
    # three points around the edge. This way you interpolate into the hole with 
    # a trained slope & curvature at the edges, otherwise you just get a flat plane.
    # With just a single row of cells around the hole you often get gaps
    # around the edges when distance > mean (.5 of the time? diagonals? worse 
    # when ewres!=nsres).
    reg = grass.region()
    res = (float(reg['nsres']) + float(reg['ewres'])) * 3 / 2

    if grass.run_command('r.buffer', input = tmp1, distances = res, out = tmp1 + '.buf') != 0:
	grass.fatal("abandoned. Removing temporary map, restoring user mask if needed:")

    grass.mapcalc("MASK=if($tmp1.buf==2,1,null())", tmp1 = tmp1)

    # now we only see the outlines of the NULL areas if looking at INPUT.
    # Use this outline (raster border) for interpolating the fill data:
    vecttmp = "vecttmp_fillnulls_" + unique
    grass.message("Creating interpolation points...")
    if grass.run_command('r.to.vect', input = input, output = vecttmp, feature = 'point'):
	grass.fatal("abandoned. Removing temporary maps, restoring user mask if needed:")

    # count number of points to control segmax parameter for interpolation:
    pointsnumber = grass.vector_info_topo(map = vecttmp)['points']

    grass.message("Interpolating %d points" % pointsnumber)

    if pointsnumber < 2:
	grass.fatal("Not sufficient points to interpolate. Maybe no hole(s) to fill in the current map region?")

    grass.message("Note: The following warnings may be ignored.")

    # remove internal MASK first -- WHY???? MN 10/2005
    grass.run_command('g.remove', rast = 'MASK')

    if grass.find_file(usermask, mapset = mapset)['file']:
	grass.message("Using user mask while interpolating")
	maskmap = usermask
    else:
	maskmap = None

    segmax = 600
    if pointsnumber > segmax:
	grass.message("Using segmentation for interpolation...")
	segmax = None
    else:
	grass.message("Using no segmentation for interpolation as not needed...")

    grass.run_command('v.surf.rst', input = vecttmp, elev = tmp1 + '_filled',
		      zcol = 'value', tension = tension, smooth = smooth,
		      maskmap = maskmap, segmax = segmax)

    grass.message("Note: Above warnings may be ignored.")

    # restoring user's mask, if present:
    if grass.find_file(usermask, mapset = mapset)['file']:
	grass.message("Restoring user mask (MASK)...")
	grass.run_command('g.rename', rast = (usermask, 'MASK'))

    # patch orig and fill map
    grass.message("Patching fill data into NULL areas...")
    # we can use --o here as g.parser already checks on startup
    grass.run_command('r.patch', input = (input,tmp1 + '_filled'), output = output, overwrite = True)

    grass.message("Filled raster map is: %s" % output)

    # write cmd history:
    grass.raster_history(output)

    grass.message("Done.")

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
