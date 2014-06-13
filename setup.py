from distutils.core import setup, Extension

module1 = Extension('editdistalign',
                    sources = ['editdistalign.c'])

setup (name = 'editdistalign',
       version = '1.0',
       description = """This module provides the editdistalign function that can be used to calculate the editdistance alignment between two sequences""",
       ext_modules = [module1])
