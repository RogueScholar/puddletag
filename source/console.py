#console.py

#Copyright (C) 2008-2009 concentricpuddle

#This file is part of puddletag, a semi-good music tag editor.

#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from optparse import OptionParser
import sys,os,shutil
from puddlestuff.findfunc import *
from puddlestuff.audioinfo import Tag
import pdb

path, PATH, FILENAME = os.path, audioinfo.PATH, audioinfo.FILENAME

class PuddleError(Exception): pass

def safe_name(name, to = None):
    """Make a filename safe for use (remove some special chars)

    If any special chars are found they are replaced by to."""
    if not to:
        to = ""
    else:
        to = unicode(to)
    escaped = ""
    for ch in name:
        if ch not in r'/\*?;"|:': escaped = escaped + ch
        else: escaped = escaped + to
    if not escaped: return '""'
    return escaped

def vararg_callback(option, opt_str, value, parser):
    assert value is None
    value = []
    rargs = parser.rargs
    while rargs:
        arg = rargs[0]

        if ((arg[:2] == "--" and len(arg) > 2) or
            (arg[:1] == "-" and len(arg) > 1 and arg[1] != "-")):
            break
        else:
            value.append(arg)
        del rargs[0]

    setattr(parser.values, option.dest, value)

def parseoptions(classes):
    parser=OptionParser()
    parser.add_option("-f","--filenames",dest="filename",action="callback",help="The filenames of the input files", callback=vararg_callback)
    parser.add_option("-p","--preview",action="store_true", dest="preview",help="Don't change anything, just print results.")
    parser.add_option("-v","--verbose",action="store_true", dest="verbose",help="Rename the directory according to your pattern.")
    #parser.add_option("-c","--continue",action="store_false", dest="cont",help="Yes, when asked.")
    for cl in classes.values():
        parser.add_option('--' + cl.command, dest='action' + cl.command, help=cl.description, action='callback', callback=vararg_callback)

    try:
        command = sys.argv[1]
    except IndexError:
        parser.print_help()
        sys.exit(0)
    (options,args)=parser.parse_args()

    actions = [{z[len('action'):]: getattr(options,z)} for z in dir(options) if z.startswith('action')]
    actions = [z for z in actions if z.values()[0] is not None]
    if not options.filename:
        print 'Dude, puddletag needs files to work on.'
        parser.print_help()
        sys.exit(0)
    return (options, actions)

class PuddleRunAction:
    name = 'RunAction'
    command = 'runaction'
    description = 'Run the specified action on the selected files.'
    usage = '--runaction Action Names'

    def setup(self, args):
        if not args:
            raise PuddleError('No Action was specified')
        temp = []
        for action in args:
            try:
                temp.extend(getActionFromName(action)[0])
            except IOError:
                raise PuddleError("The action, " + action + ", doesn't exist")
        self.funcs = temp

    def run(self, f):
        return runAction(self.funcs, f)

class Format:
    name = 'Format'
    command = 'format'
    description = 'Formats tags using a pattern'
    usage = '--format [tags...] pattern'

    def setup(self, pattern, *tags):
        self.tags = tags
        self.pattern = pattern

    def run(self, tags):
        #pdb.set_trace()
        value = tagtofilename(self.pattern, tags)
        return dict([(tag, value) for tag in self.tags])

class FileToTag:
    name = 'FileToTag'
    command = 'filetotag'
    description = 'Retrieves tag information from the filename'
    usage = 'pattern'

    def setup(self, pattern):
        self.pattern = pattern[0]

    def run(self, tags):
        return filenametotag(self.pattern, tags)


class TagToFile:
    name = 'TagToFile'
    command = 'tagtofile'
    description = 'Renames the file according to pattern'
    usage = 'pattern'

    def setup(self, pattern):
        self.pattern = pattern[0]

    def run(self, tags):
        return {'__path': tagtofilename(self.pattern, tags['__path'])}

class SetTag:
    name = 'SetTag'
    command = 'set'
    description = 'Writes the specified tags on the files.'
    usage = 'tag value [tag value]...'

    def setup(self, *args):
        arglen = len(args)
        if arglen == 0:
            raise PuddleError("Dude, I need some tags to modify.")
        elif arglen % 2 != 0:
            raise PuddleError("You tags and values aren't equal.")

        tags = args[0:arglen:2]
        values = args[1:arglen:2]
        self.tags = zip(tags,values)

    def run(self, tags):
        return dict([(tag, value) for tag, value in self.tags])


class SetMul:
    name = 'SetMul'
    command = 'setmul'
    description = 'Writes multiple values to the specified tags'
    usage = '--setmul tags::values'

    def setup(self, *args):
        for i, z in enumerate(args):
            if '::' in z: #The separator
                y = z.strip()
                if y == '::': #Something like ['what.py', 'artist', 'title', '::', 'what is ithis']
                    tags = args[:i]
                    values = args[i+1:]
                    break
                elif y.startswith('::'): #['what.py', 'artist', 'title', '::what is ithis']
                    tags = args[:i]
                    values = args[i:]
                    values[0] = values[0][2:]
                    break
                elif y.endswith('::'): #['what.py', 'artist', 'title::', 'what is ithis']
                    tags = args[:i+1]
                    tags[-1] = tags[-1][:-2]
                    values = args[i+1:]
                    break
                else: #['artist', 'title::"my name is"', 'what', 'is', 'this']
                    tag = y[:y.find('::')]
                    value = y[y.find('::') + 2:]
                    tags = list(args[:i]) + [tag]
                    values =  [value] + list(args[i+1:])
                    break
        if tags:
            self.tags = tags
        else:
            raise PuddleError("No tags were specified")
        values = values
        self.tags = [(tag, values) for tag in tags]

    def run(self, tags):
        return dict([(tag, value) for tag, value in self.tags])


def pprint(tags):
    bold = chr(0x1b) + "[1m";
    normal  = chr(0x1b) + "[0m";
    red   = chr(0x1b) + "[31m";
    temp = []
    for tag, value in tags.items():
        if not isinstance(value, basestring):
            value = u'[' + ','.join(value) + u']'
        temp.append(tag + u': ' + bold + value + normal)
    return u"\n".join(temp)

def renameFile(original, tags):
    if PATH in tags:
        if path.splitext(tags[PATH])[1] == "":
            extension = path.extsep + original["__ext"]
        else:
            extension = ""
        oldfilename = original[FILENAME]
        newpath = safe_name(tags[PATH] + extension)
        newfilename = path.join(path.dirname(oldfilename), newpath)
        os.rename(oldfilename, newfilename)
        tags[FILENAME] = newfilename
        tags[PATH] = newpath
    else:
        return {}
    return tags

def writeTags(original, tags):
    try:
        renameFile(original, tags)
    except (OSError, IOError), e:
        print "Couldn't rename to " + original[FILENAME] + ": " + e.strerror
        return

    try:
        original.update(tags)
        original.save()
    except (OSError, IOError), detail:
        sys.stderr.write(u"Couldn't write to file, " + original['__filename'] + u'\n')

classes = {'runaction': PuddleRunAction, 'set': SetTag, 'setmul': SetMul,
            'format': Format}
options, actions = parseoptions(classes)
files = options.filename
identifier = QuotedString('"') | Combine(NotAny('\\') + Word(alphanums + ' !"#$%&\'()*+-./:;<=>?@[\\]^_`{|}~'))
tags = delimitedList(identifier)
commands = []
for command, args in [action.items()[0] for action in actions]:
    #Instantiate the class for the command
    cl = classes[command]()
    try:
        cl.setup(*args)
    except PuddleError, e:
        print 'Error:', unicode(e)
        sys.exit(0)
    #except TypeError, e:
        #text = unicode(e)
        #temp = []
        #for s in ['takes exactly ', 'arguments (']:
            #i = text.rfind(s) + len(s)
            #temp.append(int(text[i:i+1]))
        #if temp[0] > temp[1]:
            #print 'Not enough arguments were specified to --' + cl.command
        #else:
            #print 'Too many arguments were specified to --' + cl.command
        print 'Usage:', cl.usage
        sys.exit(0)
    commands.append(cl.run)

for f in files:
    try:
        tag = audioinfo.Tag(f)
    except (IOError, OSError), e:
        print "Couldn't read " + f + ': ' + e.strerror
        continue
    if tag is not None:
        tags = tag.tags
        for com in commands:
            tags.update(com(tags))
        tags = audioinfo.converttag(tags)
        if options.preview:
            changes = {}
            for z in tags:
                if not (z in tag and tag[z] == tags[z]):
                    changes[z] = tags[z]
            print 'Original: \n', pprint(tag.tags), '\n'
            print 'Changes: \n', pprint(changes), '\n'
            print "Do you want to write the changes to the file? [Y/n]"
            i = raw_input()
            if i != u'n' or i != u'N':
                writeTags(tag, tags)
        elif options.verbose:
            changes = {}
            for z in tags:
                if not (z in tag and tag[z] == tags[z]):
                    changes[z] = tags[z]
            print 'Original: \n', pprint(tag.tags), '\n'
            print 'Changes: \n', pprint(changes), '\n'
            u'Now writing...' + tag['__filename']
            writeTags(tag, tags)
        else:
            writeTags(tag, tags)

