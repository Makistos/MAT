'''
Created on 15 Feb 2012

@author: poutima
'''

import yaml
import sys
import getopt
import string

RegTemplate = string.Template('''${bits}\t\t${reg_name}\t\t:\t${bit_value}\t${hex_value}\t${dec_value}\t${ascii_value}''')
 
def __usage():
    print '''Usage:
    -h, --help\tThis help text.
    -b, --base\tBase address of memory dump.
    -i, --input\tInput file (memory dump). Default: dump.reg.
    -m, --map\tRegister map file. Default: default.map.
    -r, --reg\tRegister filter. 
    -s, --sort\tSort key. Default: Offset. Set to 'key' to use the key.
    -w, --width\tWidth in bytes of each line in the memory dump. Default: 4 (32 bits).
    
    Default behaviour for the register offsets is that the memory dump 
    has been created starting from the address where the offsets are 
    calculated. So base address would be 0 in this default case. If,
    however, only a part of memory is dumped, -b can be used to give
    the base so that the offsets are fixed (argument is deducted from 
    the offsets).
    
    Register filter matches the string anywhere in the register's name. 
    
    Script will skip any registers that have offsets greater than size of
    memory dump. Also, any registers where offset < base are naturally 
    skipped.
    '''
    exit()

def __testBit(val, bit):
    ''' Checks whether bit is on or off in val and return "0" or "1" '''
    mask = 1 << int(bit)
    if (int(val, 16) & mask == 0):
        return "0"
    else:
        return "1"

def __bitRange(val, bits):
    ''' Returns a string containing the range of bits in val. '''
    retval = ''
    if len(bits) == 1:
        return str(__testBit(val, bits[0]))
    else:
        for bit in reversed(range(int(bits[0]), int(bits[1])+1)):
            retval = retval + str(__testBit(val, bit))
        # Could also leave reversed() out above and revese the result with retval[::-1], but this is more logical.
        return retval
    
def __printReg(regName, regDef, memory):
    ''' Prints the register info. '''
    bits = regDef['Bits']
    
    print "%s: %s (%s)" % (regName, regDef['Name'], memory)

    for key, bit in sorted(bits.iteritems()):
        bit_range = str(key).split('-', 2)
        bit_val = __bitRange(memory, bit_range)
        desc = bit.split('//')
        if len(bit_val) == 4:
            # If length of field is exactly 2 bytes, print the ascii value as well
            achar = chr(int(bit_val,2))
        else:
            achar = ''
        print RegTemplate.safe_substitute(
                                          bits=str(key), 
                                          reg_name=desc[0], 
                                          bit_value=bit_val, 
                                          hex_value=str(hex(int(bit_val))), 
                                          dec_value=str(int(bit_val)), 
                                          ascii_value=achar)
        if len(desc) > 1:
            print '\t' + desc[1].strip()
    print
    
def main(argv):
    
    mapFile = 'default.map'
    inputFile = 'dump.reg'
    base = "0"
    register = ''
    dataWidth = 4
    sortKey = 'Offset'
    # Read command-line options
    try:
        opts, args = getopt.getopt(argv, 'm:i:b:r:s:w:h', ['map=','input=', 'base=', 'reg=', '--sort=', 'width=', 'help'])
    except getopt.GetoptError:
        __usage()
     
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            __usage()
        if opt in ('-m', '--map'):
            mapFile = arg
        if opt in ('-i', '--input'):
            inputFile = arg
        if opt in ('-b', '--base'):
            base = arg
        if opt in ('-r', '--reg'):
            register = arg
        if opt in ('-s', '--sort'):
            if arg == 'key':
                sortKey = ''
            else:
                sortKey = arg
        if opt in ('-w', '--width'):
            dataWidth = arg
    
    # Get register definition file
    f = file(mapFile, 'r')
    regsDef = yaml.load(f)
    
    #print yaml.dump(regsDef)
    
    # Read file to list
    memory = [line.strip() for line in open(inputFile) if line.startswith('0x')]
    
    # Go through the registers
    if sortKey == '':
        sorted_list = sorted(regsDef.iteritems())
    else:
        sorted_list = sorted(regsDef.iteritems(), key=lambda x: x[1][sortKey])
    
    for key, reg in sorted_list:
        if 'Offset' in reg and key.find(register) != -1:
        # Offset is in bytes and each line contains four bytes:
            line = (int(reg['Offset'])-int(base, 16)) / dataWidth
            # Skip any registers that are before or after the range of the dump
            if len(memory) >= line and line >= 0:
                __printReg(key, reg, memory[line])

if __name__ == '__main__':
    
    main(sys.argv[1:])
    