from setuptools import setup, find_packages

setup(
    name="7Downloader",
    version="1.0.0",
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines(),
    entry_points={
        'console_scripts': [
            'mi_comando = 7Downloader:main',  # Ajusta 'mi_comando' y la ruta de tu función principal
        ],
    },
)
