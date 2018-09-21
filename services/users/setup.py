from setuptools import setup

###############################################################
# Change `name` and `packages` in line with your application! #
###############################################################
setup(
    name='users',
    packages=['users'],
    python_requires='>=3.5',
    install_requires=[
        'Flask',
    ],
    include_package_data=True,
)
