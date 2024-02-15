#! python3
# coding=utf-8
"""
ptrn - photo rename
Renames the photos under a directory by the datetime when they were taken. The
datetime info. will be extracted from the Exif metadata in the photo file. It
will also rename the live photo file pairs (XX.JPG + XX.MOV).

This Python script is designed to rename the photo files imported from IPhone.
These photos are typically named as "IMG_####", while this script will help to
rename them and hence assists with managing them. 

Last modified 2024-02-14
"""

import os   # for os.path related functions
import re   # for fitting of the datetime pattern
import exifread     # for reading Exif metadata from JPG and TIF files


# Functions

def is_date_time(
        string: str,
    ) -> True | False:
    """
    Checks if a string fits the datetime pattern 'YYYYMMDD_HHMMSS' (15
    characters), and the year 'YYYY' should be between (includes) 1970-9999.

    Parameters:
        string: A string which may contain the datetime info.
    Needs:
        modulus re.
    """
    # Regular expression to matches the datatime pattern 'YYYYMMDD_HHMMSS',
    Regex = (
        r'^(19[7-9][0-9]|20[0-9]{2}|9999)'  # year, 1970-9999
        r'(0[1-9]|1[0-2])'                  # month, 01-12
        r'(0[1-9]|[12][0-9]|3[01])'         # day, 01-31
        '_'
        r'(0[0-9]|1[0-9]|2[0-3])'   # hour, _00-_24
        r'([0-5][0-9])'             # min, 00-59
        r'([0-5][0-9])$'            # sec, 00-59
        )
    
    if re.match(Regex, string):
        return True
    else:
        return False


def select_by_exts(
    dir: str,
    f_exts: str | tuple[str] = '.jpg',
    ) -> list[str]:
    """
    Returns a list of files (strings) with desired extensions.

    Parameters:
        dir:    A string stores the path of the file directory.
        f_exts: The requested file extension (str), or a tuple containing the
                requested file extensions. The extension(s) listed will all be
                converted into lower cases before comparison using
                str.endswith(), and so this parameter is NOT case sensitive.                  
    Needs:
        modulus os.
    Returns:
        A list of strings - that is the paths with desired file extensions;
        An empty list, if no file with desired extension was found, or when
        any error happens.
    """
    # Converts all extension(s) into the lower case
    if isinstance(f_exts, str):     # when a str was given
        exts = f_exts.lower()
    elif isinstance(f_exts, tuple):     # when a tuple of strs were given
        exts = []
        for f_ext in f_exts:    # turns each extension into lower case
            exts.append(f_ext.lower())
        exts = tuple(exts)  # converts the list of extensions into a tuple
    else:   
        print(f"Error: wrong extension(s) were given: '{f_exts}'.\n")
        return []

    try:
        files = os.listdir(dir)     # reads all file paths under the folder
    except:     # when 'dir' cannot be accessed
        print(f"Error: cannot access the folder '{dir}'.\n")
        return []

    f_paths = []        # store the paths of sorted image files
    for file in files:
        # ignores capital cases in the file extensions
        if file.lower().endswith(exts):
            path = os.path.join(dir, file)
            f_paths.append(path)

    return f_paths


def filter_by_name(
    paths: str,
    f_heads: str | tuple[str] = 'IMG_',
    ) -> list[str]:
    """
    From a list of file paths, filters (removes) the file path whose basename
    fits the pattern '{head}YYYYMMDD_HHMMSS'. This can be used to simplify a
    list of file paths so that the files fitting the pattern do not need to be
    renamed again (and therefore saves the program running time).

    Parameters:
        path:   The path of the photo file to be renamed.
        f_head: The head part of the photo file's basename/path tail. This can
                be either a string or a tuple of strings, but all strings are
                case sensitive
    Needs:
        modulus datetime; for judging if a string is in a date format
        function is_date()
    Returns:
        A list of strings - that is the paths with desired file extension;
        An empty list, if no file with desired extension was found.

    PS. Examples related to file names and paths:
        "D:\\photos\\01.jpg"    path
        "D:\\photos"            folder/directory/path head
        "01.jpg"                basename/path tail
        "D:\\photos\\01"        file root              
        "01"                    file base
        ".jpg"                  format/extension
    """
    # Checks types of the input parameter f_heads
    if isinstance(f_heads, str):    # when a str was given
        f_heads = (f_heads,)    # converts into a tuple with only one str item
    elif isinstance(f_heads, list): # when a list was given
        f_heads = tuple(f_heads)
    elif not isinstance(f_heads, tuple):    # when f_heads is not a tuple
        print("Error: 'f_heads' should be a str or a tuple")
        return []
    
    f_paths = []    # to store filted paths

    for path in paths:
        basename = os.path.split(path)[1]   # gets the path tail - basename
        f_base = os.path.splitext(basename)[0]  # splits base & extension

        rename_tag = True   # this tag determines whether the file should be
                            # renamed (and so added into the list 'f_paths')

        for f_head in f_heads:
            # First, gets the datetime slice from the f_head string.
            len_head = len(f_head)
            dtm_slice = f_base[len_head : len_head+15]
# debug            print(f_head, dtm_slice, path)
            if f_base.startswith(f_head) and is_date_time(dtm_slice):
                rename_tag = False
                break   # skips those already fits the naming pattern
        
        if rename_tag:
            f_paths.append(path)

    return f_paths


def rn_by_exif(
    path: str,
    head: str = 'IMG_',
    ) -> str | None:
    """
    Rename a photo according to the datetime (yyyymmdd_hhmmss) it was taken,
    as recorded in its Exif. (e.g., IMG_20230406_175047.jpg)

    Parameters:
        path:   The path of the photo file to be renamed.
        head:   The head part of the photo file's basename/path tail. It is
                case sensitive; 'IMG_' by default.
    Needs:
        modulus os, sys, exifread.
    
    Returns:
        str:    the new path of the renamed file, if renaming is successful
        None:   if the file cannot be renamed
    """
    folder, f_basename = os.path.split(path)    # e.g. ("D:\\temp\\", "1.jpg")
    ext = os.path.splitext(f_basename)[1]       # e.g., ".jpg"

    try:
        with open(path, 'rb') as f_obj:
            tags = exifread.process_file(f_obj)     # obtains Exif tags
    except:
        print(f"Error: cannot access the image '{path}'.\n")

    tag_date = 'EXIF DateTimeOriginal'  # the tag (key) for datetime (value)

    if tag_date in tags:
        date_time = str(tags[tag_date]).replace(':','').replace(' ', '_')
        new_name = head + date_time + ext

        # Cope with the case when many photos were taken in the same second.
        index = 1
        while True:
            new_path = os.path.join(folder, new_name)
            if os.path.exists(new_path):
                new_name = head + date_time + "-" + str(index) + ext
                index += 1
            else:
                break   # loops until no repeated name

        try:    # renames the photo by the Exif date
            os.rename(path, new_path)
        except:
            print(f"Error: cannot rename '{path}' to '{new_path}'\n")
            return None
        
        return new_path
    
    else:
        print(f"- Not enough Exif info. to rename '{path}'")
        

def rn_mov(
    lmov_path: str,
    limg_path: str,
    ) -> str | None:
    """
    Rename a live photo movie file (typically a .MOV file) according to its
    belonging image file (typically a .JPG file).

    Parameters:
        lmov_path:  The path of the live photo's movie file to be renamed.
        limg_path:  The path of the live photo's image connecting to the movie
    Needs:
        modulus os.
    
    Returns:
        str:    the new path of the renamed .MOV file, if successfully renamed
        None:   if the movie file cannot be renamed
    """
    lmov_ext = os.path.splitext(lmov_path)[1]   # the live movie extension
    limg_base = os.path.splitext(limg_path)[0]  # the live image base
    new_lmov_path = limg_base + lmov_ext    # obtains new name for the movie

    try:    # renames the photo by the Exif date
        os.rename(lmov_path, new_lmov_path)
    except:
        print(f"Error: cannot rename '{lmov_path}' to '{new_lmov_path}'\n")
        return None

    return new_lmov_path


def rn_lphotos(
    limg_dir: str, 
    limg_ext: str = '.JPG',
    lmov_ext: str = '.MOV',
    f_heads: str | tuple[str] = 'IMG_',
    ):
    """
    Rename a pair of live photo files - usually a .JPG and its connected .MOV,
    both of which are under the same folder and share the same base name.
    
    Parameters:
        limg_dir:   The folder containing live photos (image and movie pairs)
        limg_ext:   The extension of live photo images (.JPG by default)
        lmov_ext:   The extension of movie files (.MOV by default) connecting
                    to the live photo image.
        f_heads:    The head part of the photo file's basename/path tail. This
                    can be either a string or a tuple of strings, but all
                    strings are case sensitive
    Needs:
        function rn_mov()
    # """
    # # When an empty list of file paths is given
    # if not img_paths:
    #     print("No image is renamed: no valid image path is found")
    #     return None

    # Confirm the following two parameters are strings
    if not isinstance(limg_ext, str):
        print(
            "Error: the live photo image extension " +
            "(limg_ext) must be a string"
            )
        return None
    if not isinstance(lmov_ext, str):
        print(
            "Error: the live photo movie extension " +
            "(lmov_ext) must be a string"
            )
        return None

    # Finds all live photo images and forms a list
    limg_paths = select_by_exts(limg_dir, limg_ext
                                )   # ljpg = live photo's image file
    limg_paths = filter_by_name(limg_paths, f_heads)

    # Finds all potential live photo (.mov + .jpg, with the same file base)
    # Movies in the list of given files.
    lmov_paths = select_by_exts(limg_dir, lmov_ext
                                )   # lmov = live photo's movie file
    lmov_paths = filter_by_name(lmov_paths, f_heads)

    len_limg_ext = len(limg_ext)    # for slice of the live image base string
    len_lmov_ext = len(lmov_ext)    # for slice of the live photo base string

    # Deals with potential live photos
    if lmov_paths:   # When the list of live .MOV files is NOT empty
        for lmov_path in lmov_paths:
            lmov_base = lmov_path[:-len_lmov_ext]   # the live movie base
        
            for limg_path in limg_paths:
                limg_base = limg_path[:-len_limg_ext]   # the live image base
                if lmov_base == limg_base:
                    print(
                        "Renaming live photo files: " +
                        f"{limg_path} and {lmov_path}"
                        )
                    
                    new_jpg = rn_by_exif(limg_path)     # renames the image

                    if new_jpg:
                        rn_mov(lmov_path, new_jpg)      # renames the movie
                    # An "else" case is not needed here, as rn_by_exif() will
                    # display warning info. when renaming of limg_path has not
                    # done.
    else:
        print("No live photo is found.")


# The Main Program
# Parameters
# The string of a file extension must begin with the dot (e.g., '.jpg').
img_dir = ".\\test"     # the folder containing the source images
f_heads = ('IMG_', 'img_', 'Img_',
           )   # files with these listed heads will be selected for renaming
img_exts = ('.jpg', '.jpeg', '.tif', '.tiff')   # as supported by exifread

# The Processe
rn_lphotos(img_dir)     # deals with the files of live photos first

# Deals with the image files again
img_paths = select_by_exts(img_dir, img_exts)
img_paths = filter_by_name(img_paths, f_heads)  # will filter the renamed

if img_paths:
    for img_path in img_paths:
        print(f"Renaming: {img_path}")
        rn_by_exif(img_path, 'IMG_')
    print("Done.")
else:
    print("No file was further renamed.")
