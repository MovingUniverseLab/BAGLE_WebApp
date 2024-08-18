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

### 3) Install BAGLE by cloning the BAGLE_Microlensing repo (Dev branch)
The BAGLE_Microlensing repository can be found here: [github link](https://github.com/MovingUniverseLab/BAGLE_Microlensing/tree/dev). Please make sure you clone the **dev branch**.
Also note that the python packages for the BAGLE will also need to be installed. 

## Running the Application
While in the BAGLE_WebApp folder, the web application can be ran locally by using the following command in terminal:
```
panel serve app.py
```
