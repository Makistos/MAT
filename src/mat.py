'''
Created on 15 Feb 2012

@author: mep
'''

import yaml
import sys
import getopt

def __usage():
    print '''Usage:
    -h, --help\tThis help text.
    -b, --base\tBase address of memory dump.
    -d, --diff\tDiff file. Generate a diff report between input file and diff file.
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
    
    A secondary mode is to use this as a diff tool that prints any differences between
    the input file (--input) and a diff file (--diff). This will print the offset and
    the values from both files. This is a handy way to figure which registers to add to
    the map file. Other parameters are discarded in this mode.
    
    '''
    exit()

def __testBit(val, bit):
    ''' Checks whether bit is on or off in val and returns "0" or "1" '''
    mask = 1 << int(bit)
    if (int(val, 16) & mask == 0):
        return "0"
    else:
        return "1"

def __bitRange(val, bits):
    ''' Returns a string containing the range of bits in val. '''
    retval = ''
    if len(bits) == 1:
        # Only one bit defined
        return str(__testBit(val, bits[0]))
    else:
        # A range of bits
        retval = ''.join(map(lambda x: __testBit(val, x), reversed(range(int(bits[0]), int(bits[1])+1))))
        # Could also leave reversed() out above and revese the result with retval[::-1], but this is more logical.
        return retval
    
def __printReg(regName, regDef, memory):
    ''' Prints the register info. '''
    
    print "%s: %s (%s)" % (regName.ljust(30), regDef['Name'].ljust(50), memory)

    if 'Bits' in regDef:
        bits = regDef['Bits']
        for key, bit in sorted(bits.iteritems()):
            achar = ''
            # Get bit range
            bit_range = str(key).split('-', 2)
            # Generate bit pattern
            bit_val = __bitRange(memory, bit_range)
            desc = bit.split('//')
            
            if len(bit_val) == 8:
                # If length of field is exactly 1 byte, print the ascii value as well
                achar = chr(int(bit_val,2))
    
            print '%-5s %s: %s %s %s %s' % \
                (key, desc[0].ljust(30), 
                 bit_val.rjust(32), 
                 hex(int(bit_val,2)).rjust(8), 
                 str(int(bit_val,2)).rjust(10), 
                 achar.rjust(2))
            # Add optional description
            if len(desc) > 1:
                print '\t' + desc[1].strip()
    print
    
def __reportDifferences(mem1, mem2):

    if len(mem1) != len(mem2):
        print "Memory sections have different size (%d - %d)" % (len(mem1), len(mem2))
        
    # Pick the shorter list as reference
    if len(mem1) > len(mem2):
        reg = mem2
        diff_reg = mem1
        print "Diff file is smaller so using it as reference"
    else:
        reg = mem1
        diff_reg = mem2
        
    for idx, val in enumerate(reg):
        if val != diff_reg[idx]:
            print "Offset %s (%s - %s)" % (str(hex(idx*4)), val, diff_reg[idx])
    
def main(argv):
    
    mapFile = 'default.map'
    inputFile = 'dump.reg'
    base = "0"
    diffFile = ''
    register = ''
    dataWidth = 4
    sortKey = 'Offset'
    # Read command-line options
    try:
        opts, args = getopt.getopt(argv, 'm:i:b:d:r:s:w:h', ['map=','input=', 'base=', 'diff=', 'reg=', '--sort=', 'width=', 'help'])
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
        if opt in ('-d', '--diff'):
            diffFile = arg
        if opt in ('-r', '--reg'):
            register = arg
        if opt in ('-s', '--sort'):
            if arg == 'key':
                sortKey = None
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
    
    if diffFile == '':
        # Go through the registers in sort order
        if sortKey == None:
            sorted_list = sorted(regsDef.iteritems())
        else:
            sorted_list = sorted(regsDef.iteritems(), key=lambda x: x[1][sortKey])
        
        for key, reg in sorted_list:
            # Trick here is that if no search string has been given it equates to '' which matches every register
            if 'Offset' in reg and key.find(register) != -1:
            # Offset is in bytes and each line contains four bytes:
                line = (int(reg['Offset'])-int(base, 16)) / dataWidth
                # Skip any registers that are before or after the range of the dump
                if len(memory) >= line and line >= 0:
                    __printReg(key, reg, memory[line])
    else:
        # Diff mode, tell differences between the two files
        memory2 = [line.strip() for line in open(diffFile) if line.startswith('0x')]
        __reportDifferences(memory, memory2)
        
if __name__ == '__main__':
    
    main(sys.argv[1:])
    