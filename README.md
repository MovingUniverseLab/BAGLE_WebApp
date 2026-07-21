# BAGLE Web Application
This is a web application designed to showcase the photometry and astrometry of most of the models from the dev-branch of **BAGLE**. It is coded entirely in Python through the use of **Panel**.

## Recommended Installation Instructions
### 1) Create a New Python Environment
This environment must use **Python >= 3.10**. We recommend creating a new conda or pip environment:
```
conda create -n bagle-webapp python=3.14 pip
conda activate bagle-webapp
```

### 2) Install BAGLE
The BAGLE_Microlensing repository and detailed installation instructions can be found here: [BAGLE GitHub](https://github.com/MovingUniverseLab/BAGLE_Microlensing/tree/dev). Install modes supported include conda, pip, and github.
```
pip install git+https://github.com/MovingUniverseLab/BAGLE_Microlensing
```

### 3) Install the BAGLE Web App
The web app is raw source code and does not include an installer. 
```
git clone https://github.com/MovingUniverseLab/BAGLE_WebApp.git
cd BAGLE_WebApp
conda install -n bagle-webapp --file requirements.txt
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
