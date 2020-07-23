import os
import json
import urllib.parse
import random, string
cwd = os.path.dirname(os.path.realpath(__file__))

print(cwd)


full_spec = None

def get_all_files(path):
    files = []
    for content in  os.listdir(path):
        full_path = os.path.join(path, content)
        if os.path.isdir(full_path):
            files += get_all_files(full_path)
        else:
            files.append(full_path)
    return files

files = get_all_files(cwd)
# print(files)


def fix_examples(d):
    if isinstance(d, dict):
        if "examples" in d.keys():
            example = d['examples'][0]
            d["example"] = example
            del d['examples']
        for k, v in d.items():
            fix_examples(v)
    if isinstance(d, list):
        for val in d: fix_examples(val)

def fix_schema(ghpath, dest):
    p = urllib.parse.unquote(ghpath).replace("https://github.com/juspay/lsp-lender-protocol-specification/blob/master/", "")
    p = os.path.join(cwd, p)
    if p not in files:
        print("Not found", p)
    schema = json.load(open(p))
    del schema["$schema"]
    del schema["$id"]
    schema_props = schema.get('properties', {})
    for pn, pv in schema_props.items():
        for pvk, pvv in pv.items():
            if pvk == "$ref":
                pv[pvk] = fix_schema(pvv, dest)
            if pvk == 'items':
                if "$ref" in pvv.keys():
                    pvv['$ref'] = fix_schema(pvv['$ref'], dest)

        fix_examples(pv)
    
    if 'required' in schema.keys() and len(schema.get('required', [])) == 0:
        del schema['required']

    saveas = "schema_" + "".join(random.choice(string.ascii_letters) for i in range(10))
    dest[saveas] = schema
    return "#/components/schemas/" + saveas
    

for i, f in enumerate(files):
    if "/api/" in f:
        spec = json.load(open(f))
        spec['components'] = {}
        spec['components']['schemas'] = {}
        spec['paths'] = {p.strip(): v for p, v in spec['paths'].items()}
        for p, v in spec['paths'].items():
            for m, vm in v.items():
                reqRef = vm['requestBody']['content']['application/json']['schema']['$ref']
                saved_as = fix_schema(reqRef, spec['components']['schemas'])
                vm['requestBody']['content']['application/json']['schema']['$ref'] = saved_as
                respRef = vm['responses']['200']['content']['application/json']['schema']['$ref']
                saved_as = fix_schema(respRef, spec['components']['schemas'])
                vm['responses']['200']['content']['application/json']['schema']['$ref'] = saved_as
        if full_spec is None:
            full_spec = spec
        else:
            full_spec['paths'].update(spec['paths'])
            full_spec['components']['schemas'].update(spec['components']['schemas'])




json.dump(full_spec, open('api.json', 'w'), indent=2)