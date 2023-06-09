from fastapi import FastAPI  
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn 
import requests
import tableauserverclient as TSC
import shutil
import kaggle  
import os 
import urllib.parse
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans 
import matplotlib.pyplot as plt
import seaborn as sns  
import io
import imgkit
import base64
import urllib.request
from tableau_api_lib.utils import querying , flatten_dict_column
from tableau_api_lib import TableauServerConnection

app = FastAPI() 

origins = [
    "http://localhost",
    "http://localhost:3000",
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Specify the Tableau Server or Tableau Online connection details
tableau_server = "https://your-tableau-server-url"
username = "your-username"
password = "your-password"
site_id = "site_id"
tableau_auth = TSC.TableauAuth(username, password, site_id)
server = TSC.Server(tableau_server)

# Tableau Server connection details



config = {
    'tableau_online': {
        'server' : "",
        "api_version": "3.19",
        "personal_access_token_name": "",
        "personal_access_token_secret" : "",
        "site_name": "",
        "site_url": "",
    }
}

connection = TableauServerConnection(config , env='tableau_online')
connection.sign_in() 

def download_datasource(url):
    parsed_url = urllib.parse.urlparse(url)

    # Extract the dataset and file name from the URL
    dataset = "/".join(parsed_url.path.split("/")[2:4])
    file_name = urllib.parse.parse_qs(parsed_url.query)['select'][0]

    # Decode the file name
    file_name = urllib.parse.unquote(file_name)
    print("URL:", file_name)

    print("Dataset:", dataset)
    print("File Name:", file_name) 

    # Download the file
    DATASET = "./dataset"
    os.makedirs(DATASET, exist_ok=True)
    kaggle.api.dataset_download_file(dataset, file_name, path=DATASET)

    # Modify the file name to replace spaces with underscores
    old_file_name = file_name.replace(" ", "%20")
    new_file_name = file_name.replace(" ", "_")
    print("New File Name:", new_file_name)

    # Rename the downloaded file to the modified file name
    downloaded_file_path = os.path.join(DATASET, old_file_name)
    print("Downloaded file path:", downloaded_file_path)
    new_file_path = os.path.join(DATASET, new_file_name)
    os.rename(downloaded_file_path, new_file_path)

    print("Downloaded file path:", new_file_path)
    return new_file_path

def clustering(url):
    data = pd.read_csv(url) 
    columns_for_clustering = data.columns.tolist() 
 
    numeric_columns = data.select_dtypes(include='number')
 
    num_columns_for_clustering = numeric_columns.columns.tolist() 
 
    numeric_columns = numeric_columns.dropna() 
    numeric_columns = numeric_columns.reset_index(drop=True) 

    features =  num_columns_for_clustering
    kmeans = KMeans(n_clusters=len(num_columns_for_clustering))
    numeric_columns['cluster'] = kmeans.fit_predict(numeric_columns[features])

    for i in range(len(num_columns_for_clustering)-1):
        sns.scatterplot(x=num_columns_for_clustering[i], y =num_columns_for_clustering[i+1], hue='cluster', data=numeric_columns) 
        plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], marker='x', color='red', label='Cluster Centers')
        plt.xlabel(num_columns_for_clustering[i])
        plt.ylabel(num_columns_for_clustering[i+1])
        plt.title(f'{num_columns_for_clustering[i]} vs {num_columns_for_clustering[i+1]}')
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.) 
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plot_data_1= base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.clf()

    # plot histogram for all features
    numeric_columns.hist(figsize=(10,10))
    plt.xlabel('Features')
    plt.ylabel('Frequency')
    plt.title('Histogram for all features')
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data_2= base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.clf()

    # line chart for  all features
    numeric_columns.plot(figsize=(7,7))
    plt.xlabel('Features')
    plt.ylabel('Frequency')
    plt.title('Line chart for all features')
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data_3= base64.b64encode(buffer.getvalue()).decode('utf-8') 
    plt.clf()

    # Aggregate the data to get the counts or proportions
    column_counts = numeric_columns['cluster'].value_counts() 
    plt.pie(column_counts, labels=column_counts.index, autopct='%1.1f%%')
    plt.title('Distribution of Cluster Values')
    plt.axis('equal')
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data_4= base64.b64encode(buffer.getvalue()).decode('utf-8') 
    plt.clf()

    return plot_data_1,plot_data_2,plot_data_3,plot_data_4

def htmlContent(data_1 , data_2 , data_3 , data_4):
    html_content = """
    <html>
    <head>
        <title>Clustering Dashboard</title>
        <style>
            .image-row {
                display: flex;
                justify-content: space-between;
            }
        </style>
    </head>
    <body>
        <h1>Clustering Dashboard</h1> 
        <div class="image-row"> 
            <img src="data:image/png;base64, {{ plot_data_1 }}" alt="Clustering Plot">
            <img src="data:image/png;base64, {{ plot_data_3 }}" alt="Clustering Plot">
        </div>
        <div class="image-row">
            <img src="data:image/png;base64, {{ plot_data_2 }}" alt="Clustering Plot">
            <img src="data:image/png;base64, {{ plot_data_4 }}" alt="Clustering Plot">
        </div>
        <p>Public sharable link</p>
    </body>
    </html>
    """

    html_content = html_content.replace("{{ plot_data_1 }}", data_1)
    html_content = html_content.replace("{{ plot_data_2 }}", data_2)
    html_content = html_content.replace("{{ plot_data_3 }}", data_3)
    html_content = html_content.replace("{{ plot_data_4 }}", data_4)

    options = {
        "format": "jpeg",
        "quality": 100
    }
    output_path = "./images/dashboard.jpg"
    imgkit.from_string(html_content, output_path, options=options)

        # Read the image file and encode it as a base64 string
    with open(output_path, "rb") as image_file:
        image_data = image_file.read()
        base64_data = base64.b64encode(image_data)
        base64_data_uri = f"data:image/png;base64,{base64_data.decode('utf-8')}"
    return output_path , base64_data_uri

def create_tableau_workbook_with_extension(connection: TSC.Server, workbook_path: str, tableau_version: str, data: pd.DataFrame):
    # Create a new Tableau workbook
    workbook = Workbook(tableau_version)
    
    # Perform necessary operations to construct the workbook
    # Create a worksheet
    worksheet = workbook.create_worksheet("Sheet 1")
    
    # Perform clustering analysis on the data
    kmeans = KMeans(n_clusters=3)
    clusters = kmeans.fit_predict(data)
    
    data_1 , data_2 , data_3 , data_4 = plot_graphs(data) 

    # Add a text mark to the worksheet
    text_mark = worksheet.add_text_mark()
    
    # Set the text mark properties
    text_mark.text = "Cluster: " + str(clusters)
    text_mark.x = 0
    text_mark.y = 0
    
    # set the graph mark properties
    graph_mark = worksheet.add_graph_mark()
    graph_mark.x = 0
    graph_mark.y = 0
    graph_mark.width = 800
    graph_mark.height = 600

    output_path , base64_data_uri = htmlContent(data_1 , data_2 , data_3 , data_4)
    # Add an image mark to the worksheet
    image_mark = worksheet.add_image_mark(output_path)

    # Set the image mark properties
    image_mark.x = 0
    image_mark.y = 0
    image_mark.width = 800
    image_mark.height = 600
    image_mark.image_uri = base64_data_uri



    # Set the workbook default view
    workbook.default_view = worksheet
    
    # Save the workbook to the specified path
    workbook.save(workbook_path)
    
    # Create a packaged workbook (.twbx) by adding a packaged data source
    packaged_workbook_path = f"{workbook_path}.twbx"
    workbook.add_packaged_datasource()
    workbook.save_as(packaged_workbook_path)
    
    # Publish the packaged workbook to Tableau Server
    connection.workbooks.publish(packaged_workbook_path, packaged_workbook_path, overwrite=True)
 

def publish_to_tableau(workbook):
    workbook = "Regional.twbx"
    with server.auth.sign_in(tableau_auth):

        # Check if the workbook already exists and delete it if it does
        for workbook in TSC.Pager(server.workbooks):
            if workbook.name == 'Cluster Results':
                server.workbooks.delete(workbook.id)

        # Create a new workbook
        new_workbook = TSC.WorkbookItem(name='Cluster Results', project_id='54b15f38-245a-4fd8-873a-424284dc1aea')

        # Set the name for the new workbook
        new_workbook.name = 'Cluster Results'

        # Publish the new workbook to the server
        new_workbook = server.workbooks.publish(new_workbook, workbook, 'Overwrite')

        # Get the ID of the newly created workbook
        new_workbook_id = new_workbook.id
    
        print('Workbook published successfully with ID:', new_workbook_id)

def create_workbook(connection: TableauServerConnection, workbook_name: str, project_id: str) -> str:
    server = Server(connection)
    workbook = server.workbooks.create(workbook_name, project_id)
    return workbook.id


def update_workbook(connection: TableauServerConnection, workbook_id: str, data_frame: pd.DataFrame, sheet_name: str):
    server = Server(connection)
    workbook = server.workbooks.get_by_id(workbook_id)
    workbook.views.update(sheet_name, data_frame)


def publish_workbook(connection: TableauServerConnection, workbook_id: str):
    server = Server(connection)
    workbook = server.workbooks.get_by_id(workbook_id)
    server.workbooks.publish(workbook)


def get_query_view_link(connection: TableauServerConnection, view_id: str) -> str:
    server = Server(connection)
    view = server.views.get_by_id(view_id)
    url = f"{server}/#/site/{site_id}/views/{view.content_url}"
    return url


@app.post("/clustering")
async def generate(txt: str ):
    print("txt",txt)

    if not txt.startswith("https://www.kaggle.com/") or "select" not in urllib.parse.parse_qs(urllib.parse.urlparse(txt).query): 
        return {
            "status": '404',
            "message": "Invalid URL. Please provide a valid Kaggle URL with a select query parameter."
        }
    else :

        with server.auth.sign_in(tableau_auth):
            url = download_datasource(txt)
            data = pd.read_csv(url) 
            columns_for_clustering = data.columns.tolist() 
        
            numeric_columns = data.select_dtypes(include='number')
        
            num_columns_for_clustering = numeric_columns.columns.tolist() 
        
            numeric_columns = numeric_columns.dropna() 
            numeric_columns = numeric_columns.reset_index(drop=True) 

            features =  num_columns_for_clustering
            kmeans = KMeans(n_clusters=len(num_columns_for_clustering))
            numeric_columns['cluster'] = kmeans.fit_predict(numeric_columns[features])

            data['cluster'] = numeric_columns['cluster']
            
            # Create clustering and bar plot
            clusters = data.groupby("cluster").size()
            bar_plot = data.plot.bar(x="cluster", y="size")

            # Save workbook as .twb file
            workbook = TSC.Workbook("DataConnect.twb")
            workbook.addWorksheet("Clusters")
            workbook.addWorksheet("Bar Plot")
            workbook.save()

            # Update workbook with clustering and bar plot
            document_update_request = TSC.UpdateDocumentRequest()
            document_update_request.set_content(workbook.to_xml())
            document_update_request.set_overwrite(True)
            document_update_job = server.updateDocument(document_update_request)
            document_update_job.wait()

            # Publish workbook to Tableau Server
            publish_job = server.publishWorkbook(workbook, "DataConnect")
            publish_job.wait()

            # Get sharable URL for workbook
            url = publish_job.getPublishUrl()

            # Publish the data CSV as a data source
            data_source = TSC.DatasourceItem()
            data_source = server.datasources.publish(url, data_source)
            
            # Create a workbook
            workbook = TSC.WorkbookItem(name="DataConnect")
            workbook = server.workbooks.create(workbook)

            # Create a clustering view
            clustering_view = TSC.ViewItem(name="Clustering", workbook=workbook)
            clustering_view.set_datasource(data_source)

            # Create a bar plot view
            bar_plot_view = TSC.ViewItem(name="Bar Chart", workbook=workbook)
            bar_plot_view.set_datasource(data_source)

            # Update the workbook with both views
            server.workbooks.populate_views(workbook)
            server.views.update(clustering_view)
            server.views.update(bar_plot_view)

            # Publish the workbook to generate a sharable URL
            server.workbooks.publish(workbook)

            # Get the workbook's sharable URL
            workbook_url = server.workbooks.get_by_id(workbook.id).content_url
            shareable_url =  f"{tableau_server}/#/site/{server.site_id}/views/{workbook_url}"
            # Print the sharable URL
            print("Sharable URL:", shareable_url)
            
        return {
            "status": '200',
            "url": shareable_url ,
            "message" : "Success"
                }


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)