from flask import Flask, request, send_file
import graphviz
import io
import json
import regex
import sys


app = Flask(__name__)


def convert_string_to_variable(string):
    """Extract Python structures from a form value (string)"""
    raw = regex.sub("'", '"', string)
    data = json.loads(raw)
    return data


@app.route("/image")
def make_graph():
    """Create the diagram and return it in png format"""
    edges_raw = regex.sub("%20", "", request.args.get("edges"))
    edges_raw = regex.sub("'", '"', edges_raw)
    edges_data = json.loads(edges_raw) 
    g = graphviz.Digraph('G', filename='graph')
    g.attr(rankdir='LR')
    g.format = 'png'
    for edge in edges_data:
        g.edge(edge[0], edge[1], label=edge[2])
    img_bytes = g.pipe(format="png")
    return send_file(
        io.BytesIO(img_bytes),
        mimetype="image/png",
    )


def form(edges):
    """Show the edge changing forms"""
    if not edges:
        edges = request.form.get("edges", "[]")
    return f"""
    <p>
    <strong>Create edge</strong>
      <form action="/process" method="post">
        <input name="input_node_name"> input node name
        <br><input name="output_node_name"> output node name
        <br><input name="label_name"> label name
        <br><input name="edges" type="hidden" value="{edges}">
        <br><input type="submit" value="Create edge">
      </form>
    </p>
    <p>
      <strong>Delete node</strong>
      <form action="/delete_node" method="post">
        <input name="node_name"> node name
        <br><input name="edges" type="hidden" value="{edges}">
        <br><input type="submit" value="Delete node">
      </form>
    </p>
    <p>
      <strong>Delete edge</strong>
      <form action="/delete_edge" method="post">
        <input name="label_name"> label name
        <br><input name="edges" type="hidden" value="{edges}">
        <br><input type="submit" value="Delete edge">
      </form>
    </p>
    <p>
      <strong>Clear graph</strong>
      <form action="/clear" method="post">
      <input name="edges" type="hidden" value="[]">
      <input type="submit" value="Clear graph">
      </form>
    </p>
    """


@app.route("/")
def render_all(edges=[], error_message=""):
    """Show the diagram, the functions, an error messge and the forms"""
    return f'<strong>Graph</strong><p><img src="/image?edges={edges}"></p>' + f"{compute_functions(edges)}" + error_message + form(edges)


@app.route("/process", methods=["POST"])
def process():
    """Process a requested change to the diagram and show the new diagram"""
    input_node_name = request.form.get("input_node_name", None)
    output_node_name = request.form.get("output_node_name", None)
    label_name = request.form.get("label_name", None)
    edges = convert_string_to_variable(request.form.get("edges", "[]"))
    if input_node_name and output_node_name and label_name:
        edges.append([input_node_name, output_node_name, label_name])
        error_message = ""
    else:
        error_message = "<p><font style='color: red'>The edge could not be created. Please fill in all three boxes.</font></p>"
    return render_all(edges, error_message)


@app.route("/clear", methods=["POST"])
def clear():
    """Delete all edges and nodes and show the new diagram"""
    return render_all([])


@app.route("/delete_node", methods=["POST"])
def delete_node():
    """Delete the node with the specified name and show the new diagram"""
    node_name = request.form.get("node_name", None)
    edges = convert_string_to_variable(request.form.get("edges", "[]"))
    if node_name:
        to_be_deleted = []
        for index, edge in enumerate(edges):
            if edge[0] == node_name or edge[1] == node_name:
                to_be_deleted.append(index)
        for index in reversed(to_be_deleted):
            edges.pop(index)
    return render_all(edges)

      
@app.route("/delete_edge", methods=["POST"])
def delete_edge():
    """Delete all edges with the specified labels and show the new diagram"""
    label_name = request.form.get("label_name", None)
    edges = convert_string_to_variable(request.form.get("edges", "[]"))
    if label_name:
        to_be_deleted = []
        for index, edge in enumerate(edges):
            if edge[2] == label_name:
                to_be_deleted.append(index)
        for index in reversed(to_be_deleted):
            edges.pop(index)
    return render_all(edges)


def make_product(edge_label_name, variable_name):
    """Create a string representing the product of a edge label and a node name"""
    if variable_name == "1":
        return edge_label_name
    else:
        return f"{edge_label_name}*{variable_name}"


def compute_functions(edges):
     """Compute mathematical functions representing the edge collection and return them as strings"""
     functions = {}
     try:
         for edge in edges:
             if edge[1] in functions:
                 functions[edge[1]] += f" + " + make_product(edge[2], edge[0])
             else:
                 functions[edge[1]] = f"{edge[1]} = {make_product(edge[2], edge[0])}"
     except:
         pass
     return f"""<br><strong>Functions</strong><p>{'<br>'.join([functions[key] for key in functions])}</p>"""
     

if __name__ == "__main__":
    print("\033[92mTo use the app: open http://localhost:8000 in your browser\033[0m")
    app.run(port=8000,  debug=False, use_reloader=False)
