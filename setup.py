from setuptools import setup, find_packages

setup(
    name='clans',
    version='2.1.0',
    packages=find_packages(),
    package_data={'clans': [
        'clans/clans/taxonomy/names.dmp',
        'clans/clans/taxonomy/rankedlineage.dmp',
        'clans/clans/GUI/icons/*.gif',
        'clans/input_example/clans_format/*',
        'clans/input_example/fasta_format/*',
        'clans/input_example/metadata/groups/*',
        'clans/input_example/metadata/numerical_features/*',
        'clans/input_example/tab_delimited_format/*',
        'clans/manual/*.pdf',
    ]},
    include_package_data=True,
    url='https://github.com/inbalpaz/CLANS',
    license='GPL',
    author='Inbal Paz',
    author_email='inbal.paz@tuebingen.mpg.de',
    description='Program for visualizing the relationship between proteins based on their pairwise sequence similarities.'
)
