# BAGLE Web Application
This is a web application designed to showcase the photometry and astrometry of most of the models from the dev-branch of **BAGLE**. It is coded entirely in Python through the use of **Panel**.

## Recommended Installation Instructions
### 1) Create a New Python Environment
This environment must use **Python >= 3.10**. 

Additionally, if you are using MacOS, there should be extra caution for the platform of the environment. Although the BAGLE Calculator will work perfectly fine with osx-arm64, you **will not** be able to use the BAGLE model fitter in its entirety. If you plan on using the latter, set the platform to osx-64 instead.

### 2) Clone the BAGLE_Microlensing Repo (Dev branch)
The BAGLE_Microlensing repository can be found here: [BAGLE GitHub](https://github.com/MovingUniverseLab/BAGLE_Microlensing/tree/dev). Please make sure you clone the **dev branch** like so:
```
git clone -b dev https://github.com/MovingUniverseLab/BAGLE_Microlensing.git
```

### 3) Install Python Packages for BAGLE_Microlensing
Navigate to the cloned BAGLE_Microlensing directory.
If your environment platform is **not** osx-arm64, you should be able to simply run one of the following commands:
```
# For pip:
pip install -r requirements.txt

# For conda/mamba:
conda install -y -c conda-forge --file requirements.txt
```
Otherwise, you will need to remove or comment out **pymultinest** from the **requirements.txt** before running the command. This is because multinest is not supported in osx-arm64.

### 4) Using BAGLE as a Python Package
Still in the BAGLE_Microlensing directory, navigate into the **src** directory and get its **absolute path** with ```pwd```.
Navigate to your **.bashrc**, **.bash_profile**, or **.zshrc** file (depending on what you use) and add
```
export PYTHONPATH=$PYTHONPATH:PATHTOBAGLE
```
where ```PATHTOBAGLE``` is the absolute path obtained from ```pwd```.

### 5) Clone the BAGLE_WebApp Repo
```
git clone https://github.com/MovingUniverseLab/BAGLE_WebApp.git
```

### 6) Install Python Packages for BAGLE_WebApp
Navigate to the cloned BAGLE_WebApp directory and run one of the commands in **3)**. Done!

</br>

## Running the Application
While in the BAGLE_WebApp directory, the web application can be ran locally with
```
panel serve app.py
```
