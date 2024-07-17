from flask import Flask, request, jsonify
import sqlglot
from flask import send_file
from sqlglot import exp
from graphviz import Digraph
import json
from flask_cors import CORS

def extract_table_relationships(parsed_ddl):
    tables = {}
    relationships = []
    table_names = ['']
    for statement in parsed_ddl:
        columns = {}
        current_table = ''
        table = ''
        ref = {}
        if isinstance(statement, exp.Create):
            snap = statement.this
            table = str(snap.this.name)
            current_table = table
            table_names.append(table)
            columns = {col.this.name: col.args.get('kind') for col in snap.expressions if isinstance(col, exp.ColumnDef)}
            ref_temp = {}
            pkc=[]
            for col in snap.expressions:
                if(col.args.get('constraints') is not None):
                    for pk in col.args.get('constraints'):
                        if('kind' in pk.args):
                            if isinstance(pk.args['kind'], exp.PrimaryKeyColumnConstraint):
                                pkc.append(col.this.name)
                if isinstance(col, exp.ColumnDef):
                    columns[col.this.name] = col.args.get('kind').this.value
                if isinstance(col,exp.PrimaryKey):
                    print(col.iter_expressions)
                if isinstance(col, exp.ForeignKey):
                    ref_temp = {}
                    ref_temp['left_table'] = table
                    for left in col.args['expressions']:
                        if 'left_table_column' not in ref_temp:
                            ref_temp['left_table_column'] = []
                        ref_temp['left_table_column'].append(left.this)
                    right_table = col.args['reference'].this.this.name
                    ref_temp['right_table'] = right_table
                    for srcCol in col.args['reference'].this.args['expressions']:
                        if 'right_table_column' not in ref_temp:
                            ref_temp['right_table_column'] = []
                        ref_temp['right_table_column'].append(srcCol.name)
                if(len(ref_temp.keys())!=0):
                    ref[right_table] = ref_temp
            tables[table] = {'columns': columns, 'foreign_keys': ref,'foreign_keys_len':len(ref.keys()),'PrimaryKey':pkc}

        elif isinstance(statement,exp.AlterTable):
            snap = statement.this
            table = snap.this.name
            for col in statement.args['actions']:
                if isinstance(col, exp.AddConstraint):
                    ref_temp = {}
                    for action in col.expressions:
                        

                        if isinstance(action,exp.ForeignKey):
                            ref_local = {}
                            ref_local['left_table']=table
                            for left in action.expressions:
                                if 'left_table_column' not in ref_local:
                                    ref_local['left_table_column'] = []
                                ref_local['left_table_column'].append(left.this)

                            right_table = action.args['reference'].this.this.name
                            ref_local['right_table'] = right_table
                            for left in action.args['reference'].this.args['expressions']:
                                if 'right_table_column' not in ref_local:
                                    ref_local['right_table_column'] = []
                                ref_local['right_table_column'].append(left.this)
                        ref[right_table] = ref_local
                        
                            # right_table = col.args['reference'].this.this.name
                            # ref_temp['right_table'] = right_table
                            # print(action.iter_expressions)
                        tables[table]['foreign_keys'] = {right_table:ref[right_table]}
                        tables[table]['foreign_keys_len'] = len(ref[right_table])
        
    #print(tables)
    return tables

def get_image(tables,lable=False,result='PNG'):
    filename = 'dag'  # Path to your image file
    dag = Digraph()
    for node in tables:
        if((tables[node]['foreign_keys_len']==0) and len(tables)==1):
            dag.node(node)
            pass
        elif((tables[node]['foreign_keys_len']==0) and len(tables)>1):
            dag.node(node)
            pass
        for dep in tables[node]['foreign_keys']:
            for column in tables[node]['foreign_keys'][dep]['right_table_column']:
                if(lable=='true'):
                    dag.edge(dep, node,label=tables[node]['foreign_keys'][dep]['left_table_column'][0]+"="+column)
                else:
                    dag.edge(dep, node)
    dag.render(filename, format='png', cleanup=True)
    if(result=='RAW'):
        return dag.source
    return send_file(filename+'.png', mimetype='image/png')

app = Flask(__name__)
CORS(app) 

@app.route('/')
def hello_world():
    return 'Hello'

@app.route('/test')
def test():
    return 'OK'

@app.route('/ER', methods=['GET', 'POST'])
def ER():
    try:
        type = request.args.get('type', 'Guest')
        query = request.args.get('query', 'Guest')
        result = request.args.get('result', 'Guest').upper()
        lable = request.args.get('lable', 'Guest').lower()
        parsed_ddl = sqlglot.parse(query)
        if type == 'ER':
            tables = extract_table_relationships(parsed_ddl)
            if(result=='JSON'):
                return json.dumps(tables)
            elif(result=='JSONRAW'):
                return tables
            elif(result in ['RAW','PNG']):
                return get_image(tables=tables,lable=lable,result=result)
        return tables
    except Exception as e:
        return e
def creteApp():
    app.run(host='0.0.0.0',port=4444)
    #app.run(debug=True)
