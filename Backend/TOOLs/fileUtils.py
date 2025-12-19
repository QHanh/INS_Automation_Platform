

# Import dependancies
import shutil, re, os, shlex

#---------------------------------------------------------------------
# everything_except
#
# Create a filter to be used to exclude file types.
#---------------------------------------------------------------------
def everything_except(*exts):
    """Filter used to exclude the given file types"""

    return lambda _, files: [f for f in files if not any(f.endswith(ext)
                                                         for ext in exts)]

class UsrFileUtils:

	# Get the list of projects in the working folder (normally one project for simplicity)
	def get_all_file_names(working_dir, file_ext):
		names = []
		for file in os.listdir(working_dir):
		    if file.endswith(file_ext):
                        names.append(file.split('.')[0])
		return names

	def everything_except(*exts):
		"""Filter used to exclude the given file types"""

		return lambda _, files: [f for f in files if not any(f.endswith(ext)
                                                                    for ext in exts)]

	def move_files(src_dir, dest_dir, *exts):
		"""Copies files from the source directory to the destination.
		Only files which match the given extension(s) are copied.
		"""
		shutil.copytree(src_dir, dest_dir, ignore=everything_except(*exts))

	def copy_files(src, dest):
		src_files = os.listdir(src)
		for file_name in src_files:
		    full_file_name = os.path.join(src, file_name)
		    if (os.path.isfile(full_file_name)):
                        shutil.copy(full_file_name, dest)

	def copy_a_file(srcdir, dstdir, ext):
                for basename in os.listdir(srcdir):
                    if basename.endswith(ext):
                        pathname = os.path.join(srcdir, basename)
                        if os.path.isfile(pathname):
                            shutil.copy2(pathname, dstdir)
						
	def remove_files_with_extensions(src, *exts):                
                for file in os.listdir(src):
                    if file.endswith(tuple(exts)):
                        os.remove(os.path.join(src, file))
                        
	def read_inf_file(infFileName):
                chans = []
                with open(infFileName) as f:
                    for l in f:
                        ll = shlex.split(l.strip())
                        cr = {}
                        indre = re.match('PGB\(([0-9]*)\)', ll[0])
                        if indre: cr['index'] = int(indre.group(1))
                        for t in ll:
                            tt = t.split('=')
                            if len(tt) > 1: cr[tt[0]] = tt[1]
                            #
                        kk = cr['Desc'].split(':') # group all signals in a channel by channel name and indexes
                        if len(kk) > 1: cr['Desc'] = {int(kk[1]):kk[0]}
                        else: cr['Desc'] = {0:kk[0]}

                        if len(cr) > 0: chans.append(cr)
                return chans

