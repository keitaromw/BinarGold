from flask import Flask,request,render_template
from flask import jsonify,redirect,url_for
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
import re
import pandas as pd
import os
from os.path import join, dirname, realpath
import sqlite3 

app = Flask(__name__)

app.json_encoder = LazyJSONEncoder
swagger_template = dict(
    info = {
        'title': LazyString(lambda: 'API Documentation for CSV and Text Cleansing'),
        'version': LazyString(lambda: '1.0.0'),
        'description': LazyString(lambda: 'Documentation of the CSV and Text Cleaning API')
    },
    host = LazyString(lambda: request.host)
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json'
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template,config=swagger_config)

# enable debugging mode
app.config["DEBUG"] = True

# Upload folder
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

#Database
conn = sqlite3.connect('docs/temp.db', check_same_thread=False)
c = conn.cursor()

#Alay dictionary
alay_dict = pd.read_csv('static/new_kamusalay.csv', encoding='latin-1', header=None)
alay_dict = alay_dict.rename(columns={0: 'original', 
                                      1: 'replacement'})

#Abusive word
abusive_dict = pd.read_csv('static/abusive.csv', encoding='latin-1')
abusive_list = abusive_dict['ABUSIVE'].tolist()
#Change the abusive words into "****"
def normalize_abuse(text):
    compile_list =  re.compile("|".join(abusive_list))
    return compile_list.sub("****", text)


#Create a dictionary from the new_kamisalay.csv
alay_dict_map = dict(zip(alay_dict['original'], alay_dict['replacement']))
def normalize_alay(text):
    return ' '.join([alay_dict_map[word] if word in alay_dict_map else word for word in text.split(' ')])

# Clean text function
def clean_function(text):
    text = text.lower() # Change all to lowercase
    text = re.sub('\n',' ',text) # Remove '\n'
    text = re.sub('[^0-9a-zA-Z]+', ' ', text) # remove non alphanumerical
    text = re.sub('rt',' ',text) # Remove rt
    text = re.sub('user',' ',text) # Remove user
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))',' ',text) # Remove URL

    #Remove x.. sequence of unecessary word
    text = re.sub('xe5',' ',text)
    text = re.sub('xbc',' ',text)
    text = re.sub('xa0',' ',text)
    text = re.sub('xe8',' ',text)
    text = re.sub('x89',' ',text)
    text = re.sub('xba',' ',text)
    text = re.sub('xe2',' ',text)
    text = re.sub('x80',' ',text)
    text = re.sub('x99',' ',text)
    text = re.sub('xf0',' ',text)
    text = re.sub('x9f',' ',text)
    text = re.sub('x98',' ',text)
    text = re.sub('x82',' ',text)
    text = re.sub('x84',' ',text)
    text = re.sub('x8f',' ',text)
    text = re.sub('x86',' ',text)
    text = re.sub('xc2',' ',text)
    text = re.sub('xb2',' ',text)
    text = re.sub('xa2',' ',text)
    text = re.sub('xa4',' ',text)
    text = re.sub('x9d',' ',text)
    text = re.sub('x8b',' ',text)
    text = re.sub('x8e',' ',text)
    text = re.sub('xb6',' ',text)
    text = re.sub('xa7',' ',text)
    text = re.sub('xab',' ',text)
    text = re.sub('xaa',' ',text)

    text = re.sub('  +', ' ', text) # Remove extra spaces 
    text = normalize_alay(text) # Compare with the alay_dict
    text = normalize_abuse(text) # Compare with the abusive_list
    
    return text


#Start/Home Route
@swag_from("docs/home.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def my_form():
    json_response = {
        'status_code': 200,
        'description': "Home Page",
        'data': "Home Page"
    }

    jsonify(json_response)

    return render_template('form.html')


#Text form cleansing
@swag_from("docs/textcleansing.yml", methods=['POST'])
@app.route('/text_cleansing', methods=['POST'])
def clean_text():
    text = request.form['t'] # Get the text input
    text = clean_function(text) # Clean the text

    json_response = {
        'status_code': 200,
        'description': "Cleaned text",
        'data': clean_function(text)
    }

    jsonify(json_response)

    return text


#CSV form cleansing
@swag_from("docs/csvcleansing.yml", methods=['POST'])
@app.route('/csv_cleansing', methods=['POST'])
def upload_and_clean():
    # Get the CSV file input
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        # Set the path
        uploaded_file.save(file_path)

    #Use pandas to create dataframe from the csv file
    csvData = pd.read_csv(file_path, encoding='latin-1')
    csvData['Tweet'] = csvData['Tweet'].apply(clean_function) # Clean the csv file on the 'Tweet' column
    li = csvData['Tweet'].head(15).tolist() # Take the head of the cleaned dataframe 

    #Create table for the database
    c.execute('CREATE TABLE IF NOT EXISTS temporary (tweet TEXT,hs INTEGER,abusive INTEGER,hs_individual INTEGER,hs_group INTEGER,hs_religion INTEGER,hs_race INTEGER,hs_physical INTEGER,hs_gender INTEGER,hs_other INTEGER,hs_weak INTEGER,hs_moderate INTEGER,hs_strong INTEGER)')
    conn.commit()

    #Temporary dataframe to change to sql format
    tempData = csvData
    tempData.to_sql('temporary', conn, if_exists='replace', index = False) # Save dataframe to the table 

    json_response = {
        'status_code': 200,
        'description': "Cleaned CSV",
        'data': csvData['Tweet'].head(15).tolist()
    }

    jsonify(json_response)
 
    return li



if __name__ == "__main__":
    app.run(port = 5000)