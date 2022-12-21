import os
import json
import subprocess
from subprocess import Popen
from django.shortcuts import render
from django.views import View
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http.response import HttpResponse, Http404


def json_extract(obj, key):
    arr = []

    def extract(obj, arr, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


def update_data(data, updated_data):
    if type(data) is dict:
        for k, v in data.items():
            if k in updated_data:
                for k1, v1 in updated_data.items():
                    if k1 in data:
                        if type(data[k1]) != dict:
                            data[k1] = v1
            else:
                update_data(v, updated_data)
    elif type(data) is list:
        for i in data:
            update_data(i, updated_data)

    return data


class UpdateJSON(View):

    def get(self, request):
        return render(request, 'index.html')

    def post(self, request):
        action = request.POST.get('action', 0)
        if action == '1':
            try:
                temp_file = request.FILES['json_file']
                if os.path.exists(os.path.join(settings.MEDIA_ROOT, temp_file.name)):
                    os.remove(os.path.join(settings.MEDIA_ROOT, temp_file.name))

                file_system_storage = FileSystemStorage()
                filename = file_system_storage.save(temp_file.name, temp_file)
                # uploaded_file_url = file_system_storage.url(filename)
                with open(os.path.join(settings.MEDIA_ROOT, filename), 'r') as f:
                    show_data = f.read()

                return render(request, 'index.html', {
                    'filename': filename, 'show_data': show_data
                })
            except Exception as e:
                return render(request, 'index.html', {'error': str(e)})

        elif action == '2':
            try:
                keys_to_update = request.POST.get('keys_to_update')
                keys_to_update = [i.strip() for i in keys_to_update.split(',') if i]
                filename = request.POST.get('filename')

                if not os.path.exists(os.path.join(settings.MEDIA_ROOT, filename)):
                    return render(request, 'index.html', {'error', 'file not exists!'})

                with open(os.path.join(settings.MEDIA_ROOT, filename), 'r') as f:
                    show_data = f.read()
                    data = json.loads(show_data)
                    s = ''
                    for key in keys_to_update:
                        extracted_data = json_extract(data, key)
                        extracted_data = extracted_data[0] if extracted_data else ''
                        if type(extracted_data) is str:
                            extracted_data = f'"{extracted_data}"'
                        s += key + ' = '+str(extracted_data) + '\n'

                    return render(request, 'index.html', {
                        'filename': filename, 'keys_to_update': ', '.join(keys_to_update), 'show_data': show_data, 'script_block': s
                    })
            except IsADirectoryError as e:
                return render(request, 'index.html', {'error': 'Please upload a file before proceed!'})
            except Exception as e:
                return render(request, 'index.html', {'error': e})

        elif action == '3':
            try:
                temp_keys = request.POST.get('keys_to_update', '')
                filename = request.POST.get('filename')
                script_block = request.POST.get('script_block')

                with open(os.path.join(settings.MEDIA_ROOT, filename), 'r') as f:
                    show_data = json.loads(f.read())

                if not temp_keys.strip():
                    return render(request, 'index.html', {
                        'filename': filename,
                        'keys_to_update': ', '.join(script_block),
                        'show_data': json.dumps(show_data, indent=4),
                        'script_block': script_block,
                        'error': 'please add atleast 1 key to update.'
                    })

                temp_keys = [i.strip() for i in temp_keys.split(',') if i]
                keys_to_update = []
                for i in temp_keys:
                    i = i.strip()
                    if '=' in i:
                        f = '==' in i or '!=' in i or '>=' in i or '<=' in i or '!=' in i or 'in' in i or 'not' in i
                        if not f:
                            keys_to_update.append(i)

                temp = script_block.split("\n")
                l = [i.split("=")[0].strip().replace(" ", "") for i in temp if i and "=" in i]
                s = set([i for i in l if i.isalpha() or i.isalnum()])

                script_name = os.path.join(settings.MEDIA_ROOT, filename + '_script.py')
                script_name = script_name.replace('(', '').replace(')', '').replace(' ', '')

                with open(script_name, 'w') as f:
                    f.write(script_block)

                    dict_str = '\ndata = {'
                    for i in s:
                        dict_str += f'"{i}": {i}, '
                    dict_str += '}\n'

                    f.write(dict_str)
                    f.write('\nimport json')
                    f.write('\nprint(json.dumps(data))\n')

                # this will run the shell command `cat me` and capture stdout and stderr
                proc = Popen(["python3", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # this will wait for the process to finish.
                proc.wait()
                read_data = proc.stdout.read().decode()
                read_err = proc.stderr.read().decode()
                if read_err:
                    context = {
                        'filename': filename,
                        'show_data': {},
                        'keys_to_update': ', '.join(temp_keys),
                        'script_block': script_block,
                        'error': read_err
                    }
                    return render(request, 'index.html', context)
                else:
                    updated_data = json.loads(read_data)

                show_data = update_data(data=show_data, updated_data=updated_data)

                with open(os.path.join(settings.MEDIA_ROOT, filename), 'w') as f:
                    f.write(json.dumps(show_data, indent=4))

                context = {'filename': filename, 'show_data': json.dumps(show_data, indent=4), 'keys_to_update': ', '.join(temp_keys), 'script_block': script_block}
                return render(request, 'index.html', context)
            except IsADirectoryError as e:
                return render(request, 'index.html', {'error': 'Please upload a file before proceed!'})
            except Exception as e:
                return render(request, 'index.html', {'error': e})

        return render(request, 'index.html', {'error': 'Invalid action!'})


def download(request, path):
    try:
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/force-download")  # content_type="application/json")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
    except:
        pass
    raise Http404
