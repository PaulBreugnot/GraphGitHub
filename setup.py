from setuptools import setup, find_packages

setup(name='graphGitHub',
      version='0.1',
      url='https://github.com/PaulBreugnot/GraphGitHub',
      author="Paul Breugnot",
      author_email='breugnot.paul@gmail.com',
      description="Data fetching from GitHub using REST or GraphQL",
      packages=find_packages(exclude=['test']),
      package_data={'graphGitHub': ['graphql_query.txt']},
      long_description=open('README.md').read(),
      install_requires=['requests', 'matplotlib']
      )
