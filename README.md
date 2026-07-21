# BAGLE Web Application
This is a web application designed to showcase the photometry and astrometry of most of the models from the dev-branch of **BAGLE**. It is coded entirely in Python through the use of **Panel**.

## Recommended Installation Instructions
### 1) Create a New Python Environment
This environment must use **Python >= 3.10**. 

Additionally, if you are using MacOS, there should be extra caution for the platform of the environment. Although the BAGLE Calculator will work perfectly fine with osx-arm64, you **will not** be able to use the BAGLE model fitter in its entirety. If you plan on using the latter, set the platform to osx-64 instead.

### 2) Install BAGLE
The BAGLE_Microlensing repository and detailed installation instructions can be found here: [BAGLE GitHub](https://github.com/MovingUniverseLab/BAGLE_Microlensing/tree/dev). Install modes supported include conda, pip, and github.
```
conda install bagle
```

### 3) Install the BAGLE Web App
```
pip install git+https://github.com/MovingUniverseLab/BAGLE_WebApp.git
```

### 4) Start the BAGLE WebApp
Open your terminal, navigate to your file's folder, and run the local development server: 
```
panel serve app.py --dev
```
Open the provided local URL (usually http://localhost:5006/app) in your web browser.

</br>

## Running the Application
While in the BAGLE_WebApp directory, the web application can be ran locally with
```
panel serve app.py
```
