from setuptools import setup

setup(
    name='clans',
    version='v2.0.1_beta',
    packages=['clans', 'clans.io', 'clans.io.file_formats', 'clans.GUI', 'clans.layouts', 'clans.graphics',
              'clans.taxonomy', 'clans.similarity_search'],
    url='https://github.com/inbalpaz/CLANS',
    license='GPL',
    author='Inbal Paz',
    author_email='inbal.paz@tuebingen.mpg.de',
    description='Program for visualizing the relationship between proteins based on their pairwise sequence similarities.'
)
