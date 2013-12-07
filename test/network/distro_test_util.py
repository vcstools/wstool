def ros_found_in_yaml(yaml_elements):
    '''
    Checks whether given yaml contains an element we can identify as ros stack
    '''
    ros_found = False
    print(yaml_elements)
    for elt in yaml_elements:
        scm_found = False
        for scm in ['svn', 'tar', 'git', 'hg']:
            if scm in elt:
                scm_found = True
                element = elt[scm]
                if element.get("local-name", "") == "ros":
                    ros_found = True
                    break
        if not scm_found:
            if "other" in elt:
                element = elt["other"]
                if element.get("local-name", "").endswith('/ros'):
                    ros_found = True
    return ros_found


def ros_found_in_path_spec(specs):
    ros_found = False
    for spec in specs:
        if spec.get_path().endswith('ros'):
            ros_found = True
            break
    return ros_found
