from setuptools import setup

###############################################################
# Change `name` and `packages` in line with your application! #
###############################################################
setup(
    name='hydra_login2f',
    packages=['hydra_login2f'],
    python_requires='>=3.5',
    install_requires=[
        'Flask',
    ],
    include_package_data=True,
)
