import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="predicted-runway",
    version="0.0.1",
    author="EUROCONTROL (SWIM)",
    author_email="francisco-javier.crabiffosse.ext@eurocontrol.int",
    description="Web Application of the InnoHub Predicted Runway In-Use project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eurocontrol-swim/predicted-runway-api",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'Flask>=2.0.2',
        'pandas>=1.4.0',
        'numpy>=1.22.1',
        'Werkzeug==2.0.2',
        'tzdata==2021.5',
        'tzlocal==4.1',
        'scikit-learn==1.0.2',
        'scipy==1.8.0',
        'holidays==0.13',
        'connexion[swagger-ui]',
        'marshmallow',
        'mongoengine',
        'flask-cors',
        'predicted-runway-met-update-db @ git+https://git@github.com/eurocontrol-swim/predicted-runway-met-update-db.git'
    ],
)
