# ANoobs Brres Material Tool (ABMatT)
This command line tool is for editing materials in _Brres_ files in _Mario Kart Wii_. Python is required to run it. The tool can do quick edits from the command line, or read in a command file for processing multiple setting adjustments. This is particularly useful for editing a large amount of materials or recreating a brres multiple times. Python regular expression matching is supported.

## Known Limitations
ABMatT currently only supports overwriting data, not additions or deletions.

## Transparency
The tool is also smart about adjusting transparency. When setting materials to transparent it also updates the comparison and reference settings, and the draw list to be xlu (fixing Harry Potter effect). These settings can also be adjusted individually, including draw priority.

## Command Line Usage
```
./AbMatT.py -f <file> [-d <destination> -o -c <commandfile> -k <key> -v <value> -n <name> -m <model> -i]
```
| Flag |Long version| Description |
|---|---|---|
| -c | --commandfile | File with ABMatT commands to be processed as specified in file format. |
| -d | --destination | The file name to be written to. Mutliple destinations are not supported. |
| -f | --file | The brres file name to be read from |
| -h | --help | Displays a help message about program usage. |
| -i | --info | Information flag that generates additional informational output. |
| -k | --key | Setting key to be updated. See [File Format](## File Format) for optional keys. |
| -m | --model | The name of the model to search in. |
| -n | --name | Material or layer name or regular expression to be found. |
| -o | --overwrite | Overwrite existing files. The default is to not overwrite the input file or any other file unless this flag is used. |
| -v | --value | Setting value to be paired with a key. |

### Command Line Examples
This command would open *course_model.brres* in overwrite mode and run the commands stored in *my_commands.txt*
```
./AbMatT.py -f course_model.brres -o -c my_commands.txt
```
This next command would update all materials starting with the prefix xlu to transparent settings.
```
./AbMatT.py -f course_model.brres -o xlu.* -k xlu -v true
```

## File Format
ABMatT supports reading in external commands from files which have a specified extended BNF format.
```
command = set | info;
set   = 'set' space key ':' value [space 'for' space name] [space 'in' space container] EOL;
info  = 'info' [space key] [space 'for' space name] [space 'in' space container] EOL;
key   = 'xlu' | 'transparent' | 'ref0' | 'ref1' |
  'comp0' | 'comp1' | 'comparebeforetexture' | 'blend' |
  'blendsrc' | 'blendlogic' | 'blenddest' | 'constantalpha' |
  'cullmode' | 'shader' | 'shadercolor' | 'lightchannel' |
  'lightset' | 'fogset' | 'matrixmode' | 'enabledepthtest' |
  'enabledepthupdate' | 'depthfunction' | 'drawpriority' |
  'scale' | 'rotation' | 'translation' | 'scn0cameraref' |
  'scn0lightref' | 'mapmode' | 'uwrap' | 'vwrap' |    
  'minfilter' | 'magfilter' | 'lodbias' | 'anisotrophy' |
  'clampbias' | 'texelinterpolate' | 'projection' | 'inputform' |
  'type' | 'coordinates' | 'embosssource' | 'embosslight' |
  'normalize';
value     = 'true' | 'false' | number-list | cull-mode | light-channel | const-alpha | matrix-mode | blend-logic | blend-factor | wrap-mode | minfilter | map-mode | projection | inputform | type | coordinates;
  number-list   = number {, number};
  cull-mode     = 'all' | 'inside' | 'outside' | 'none';
  light-channel = 'vertex' | 'ambient';
  const-alpha   = 'enable' | 'disable' | number;
  matrix-mode   = 'maya' | 'xsi' | '3dsmax';
  comparison    = 'never' | 'less' | 'equal' | 'lessorequal' |  
    'greater' | 'notequal' | 'greaterorequal' | 'always';
  blend-logic   = 'clear' | 'and' | 'reverseand' | 'copy' |
    'inverseand' | 'nooperation' | 'exclusiveor' | 'or' | 'notor' | 'equivalent' | 'inverse' | 'reverseor' | 'inversecopy' | 'inverseor' | 'notand' | 'set';
  blend-factor  = 'zero' | 'one' | 'sourcecolor' | 'inversesourcecolor'
    | 'sourcealpha' | 'inversesourcealpha' | 'destinationalpha' | 'inversedestinationalpha';
  wrap-mode     = 'clamp' | 'repeat' | 'mirror';
  minFilter     = 'nearest' | 'linear' | 'nearest_mipmap_nearest' |
    'linear_mipmap_nearest' | 'nearest_mipmap_linear' | 'linear_mipmap_linear';
  map-mode      = 'texcoord' | 'envcamera' | 'projection' | 'envlight'  
    | 'envspec';
  projection    = 'st' | 'stq';
  inputform     = 'ab11' | 'abc1';
  type          = 'regular' | 'embossmap' | 'color0' | 'color1';
  coordinates   = 'geometry' | 'normals' | 'colors' | 'binormalst' |    
    'binormalsb' | 'texcoord0' | 'texcoord1' | 'texcoord2' | 'texcoord3'  | 'texcoord4' | 'texcoord5' | 'texcoord6' | 'texcoord7';

container = ['file' space filename] ['model' space name] ['material' space name];
name      = string | regex {',' space string | regex};
space     = ? US-ASCII character 32 ?;
EOL       = [\r] \n | EOF;
```

### Example File Commands

Example file commands:
```
set transparent:true for xlu.* in model course      # Sets all materials in course starting with xlu to transparent
set shader:3 for ef_dushboard   # set any material in any model found matching 'ef_dushboard' to shader 3
set scale:(1,1)                 # Sets the scale for all layers to 1,1
```
