import csv
import json
import argparse


def get_version_compare_key(app_version):
    compare_key = ""
    if app_version is not None:
        if app_version.startswith("=="):
            compare_key = "=="
        if app_version.startswith("!="):
            compare_key = "!="
        elif app_version.startswith("=>") or app_version.startswith(">="):
            compare_key = ">="
        elif app_version.startswith(">"):
            compare_key = ">"
        elif app_version.startswith("<=") or app_version.startswith("=<"):
            compare_key = "<="
        elif app_version.startswith("<"):
            compare_key = "<"
        app_version = app_version.strip(compare_key)
    return compare_key, app_version


def compare_version(version1, version2, compare_key):
    v1 = get_digits_from_string(version1)
    v2 = get_digits_from_string(version2)
    return eval(f"{v1} {compare_key} {v2}")


def get_digits_from_string(s):
    return int("".join([x for x in s if x.isdigit()]))
    

def equal_lists(l1, l2, verbosity):
    if len(l1) != len(l2):
        return False
    l1.sort()
    l2.sort()
    for i1, i2 in zip(l1, l2):
        if not equal(i1, i2, verbosity):
            return False
    return True


def equal_dicts(d1, d2, verbosity):
    keys_set1 = set(d1.keys())
    keys_set2 = set(d2.keys())
    if len(keys_set1 & keys_set2) != len(keys_set1) or len(keys_set1) != len(
            keys_set2):
        return False

    for k in d1.keys():
        if not equal(d1[k], d2[k], verbosity):
            return False
    return True


def equal_obj(o1, o2, verbosity):
    if type(o1) != type(o2):
        return False
    return o1 == o2


def equal(obj1, obj2, verbosity=False):
    if isinstance(obj1, list) and isinstance(obj2, list):
        return equal_lists(obj1, obj2, verbosity)

    if isinstance(obj1, dict) and isinstance(obj2, dict):
        return equal_dicts(obj1, obj2, verbosity)

    return equal_obj(obj1, obj2, verbosity)


def get_data_by_template(template, data, verbosity=False):
    def matches(template, data):
        if template == {}:
            return True
        for k in template.keys():
            if k not in data.keys():
                return False

        for k in template.keys():
            if not equal(template[k], data[k], verbosity):
                return False
        return True

    return list(filter(lambda r: matches(template, r), data))


def get_serials_by_app(package_name=None, app_name=None, app_version=None):

    compare_key, version = get_version_compare_key(app_version)
    app_version = version

    template = {}
    result = []
    if package_name is not None:
        template.update({'packageName': package_name})
    if app_name is not None:
        template.update({'appName': app_name})
    if app_version is not None and not compare_key:
        template.update({'versionName': app_version})
    elif compare_key:
        for x in csv_data:
            if not isinstance(x['apps'], str)\
                    and x['apps'] \
                    and get_data_by_template(template, x['apps']) \
                    and compare_version(version1=get_data_by_template(template, x['apps'])[0]['versionName'],
                                        version2=app_version,
                                        compare_key=compare_key):
                result.append(x['serial'])
        return result

    for i in csv_data:
        _apps = i['apps']
        if _apps is not None and not isinstance(_apps, str):
            if get_data_by_template(template, _apps):
                result.append(i['serial'])
    return result


def get_serials_by_model_and_rom(model=None, rom=None):
    result = []
    for i in csv_data:
        try:
            if model is None and rom is None:
                result.append(i['serial'])
                continue
            elif model is not None and rom is not None:
                if model in i['model'] and rom in i['rom']:
                    result.append(i['serial'])
                    continue
            elif (model is not None and model in i['model'])\
                    or\
                 (rom is not None and rom in i['rom']):
                result.append(i['serial'])
        except Exception as e:
            pass
    return result


def get_data_from_csv(filename):
    data = []
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file,
                                    fieldnames=['serial', 'model', 'rom',
                                                'apps_count', 'apps'])

        for row in csv_reader:
            dct = dict(row)
            if dct['apps'] is not None:
                try:
                    dct['apps'] = json.loads(dct['apps'])
                except Exception as e:
                    pass
            data.append(dct)
    return data


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', help='Path to CSV Sunmi report')
    parser.add_argument('-m', '--model', help="Full model name or part name, like V1s, P1, etc")
    parser.add_argument('-r', '--rom', help="Firmware version of device")
    parser.add_argument('-p', '--package', help="Application package name")
    parser.add_argument('-n', '--name', help="Name of application")
    parser.add_argument('-v', '--version', help="Version of application or package name, can take prefixes like <, >, =>, <=")

    options = parser.parse_args()

    csv_data = get_data_from_csv(options.filename)
    apps = get_serials_by_app(package_name=options.package,
                              app_name=options.name,
                              app_version=options.version)
    models = get_serials_by_model_and_rom(model=options.model, rom=options.rom)

    result_list = list(set(apps) & set(models))
    result_list.sort()

    print("********** OUTPUT **********")
    print('\n'.join(result_list))
    print("********** END **********")
    print(f'TOTAL: {len(result_list)}')
    print(f"Search parameters:")
    print(f'\n'.join(['- {}: {}'.format(x[0], 'Any' if x[1] is None else x[1]) for x in vars(options).items()]))



