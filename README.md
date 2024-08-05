# BAGLE Web Application
This is a web application designed to showcase the photometry and astrometry of most of the models from the dev-branch of BAGLE.

## Installation Instructions
### 1) Clone the BAGLE_WebApp Repo
```
git clone https://github.com/MovingUniverseLab/BAGLE_WebApp.git
```

### 2) Install Python Packages for BAGLE_WebApp
Navigate to the cloned BAGLE_WebApp folder and use the following command:
```
pip install -r requirements.txt
```

### 3) Clone BAGLE_Microlensing Repo
Still in the BAGLE_WebApp folder, clone the **dev branch** of the BAGLE_Microlensing repository:
```
git clone -b dev https://github.com/MovingUniverseLab/BAGLE_Microlensing.git
```

Note that the python packages for the BAGLE_Microlensing repository will also need to be installed. 
Please refer to [BAGLE github](https://github.com/MovingUniverseLab/BAGLE_Microlensing/tree/dev) for additional information.
```
Main Packages to Install:
  - pip3 install matplotlib
  - pip3 install numpy
  - pip3 install astropy
  - pip3 install pytest
  - pip3 install celerite
  - pip3 install ephem
  - pip3 install pymultinest
```

## Running the Application
The web application can be ran locally by using the following command in terminal:
```
panel serve app.py
```
