import os
import sys
import configparser
import markdown
import shutil

from markdown.inlinepatterns import InlineProcessor
from markdown.extensions     import Extension
import xml.etree.ElementTree as etree

class markdown_strikethrough(InlineProcessor):
    def handleMatch(self,m,data):
        el      = etree.Element("del")
        el.text = m.group(1)
        return el,m.start(0),m.end(0)

class markdown_superscript(InlineProcessor):
    def handleMatch(self,m,data):
        el      = etree.Element("sup")
        el.text = m.group(1)
        return el,m.start(0),m.end(0)

class markdown_subscript(InlineProcessor):
    def handleMatch(self,m,data):
        el      = etree.Element("sub")
        el.text = m.group(1)
        return el,m.start(0),m.end(0)

class markdown_inserted_text(InlineProcessor):
    def handleMatch(self,m,data):
        el      = etree.Element("ins")
        el.text = m.group(1)
        return el,m.start(0),m.end(0)

class markdown_marked_text(InlineProcessor):
    def handleMatch(self,m,data):
        el      = etree.Element("mark")
        el.text = m.group(1)
        return el,m.start(0),m.end(0)

class markdown_custon_container(InlineProcessor):
    def __init__(self,pattern,md):
        super().__init__(pattern,md)

    def handleMatch(self,m,data):
        container_type = m.group(1).strip()
        container_text = m.group(2)

        container = etree.Element("div")
        container.set("class","custom-container")

        inner_div = etree.SubElement(container,"div")
        inner_div.set("class",container_type)

        header_text      = etree.Element("p")
        header_text.text = container_type
        header_text.set("class","container-header")

        inner_div.append(header_text)

        inner_content      = etree.Element("p")
        inner_content.text = container_text.strip()
        inner_div.append(inner_content)

        return container,m.start(0),m.end(0)

class markdown_custom_style_text(InlineProcessor):
    def handleMatch(self,m,data):
        styles = m.group(1).replace("=",":")
        text   = m.group(2)
        el     = etree.Element("span")
        el.text = text
        el.set("style",styles)
        return el,m.start(0),m.end(0)

class markdown_custom_block_style_text(InlineProcessor):
    def handleMatch(self,m,data):
        styles = m.group(1).replace("=",":")
        text = m.group(2)
        el = etree.Element("div")
        el.text = text
        el.set("style",styles)
        return el,m.start(0),m.end(0)

class markdown_url_processor(InlineProcessor):
    def handleMatch(self,m,data):
        url = m.group(0)
        el  = etree.Element("a")
        el.text = url
        el.set("href", url)
        return el,m.start(0),m.end(0)

class epic_markdown_extension(Extension):
    def extendMarkdown(self, md):
        DEL_PATTERN = r"~~(.*?)~~"
        md.inlinePatterns.register(markdown_strikethrough(DEL_PATTERN,md),"del",175)

        SUP_PATTERN = r"\^(.*?)\^"
        md.inlinePatterns.register(markdown_superscript(SUP_PATTERN,md),"sup",175)

        SUB_PATTERN = r"~(.*?)~"
        md.inlinePatterns.register(markdown_subscript(SUB_PATTERN,md),"sub",175)

        INS_PATTERN = r"\+\+(.*?)\+\+"
        md.inlinePatterns.register(markdown_inserted_text(INS_PATTERN,md),"ins",175)

        MARK_PATTERN = r"==(.*?)=="
        md.inlinePatterns.register(markdown_marked_text(MARK_PATTERN,md),"mark",175)

        CONTAINER_PATTERN = r":::(\S+)\s(.*?):::"
        md.inlinePatterns.register(markdown_custon_container(CONTAINER_PATTERN,md),"custom_container",175)

        CUSTOM_STYLE_PATTERN = r"\[(.*?)\]\[(.*?)\]"
        md.inlinePatterns.register(markdown_custom_style_text(CUSTOM_STYLE_PATTERN,md),"custom_style",174)

        CUSTOM_BLOCK_STYLE_PATTERN = r"\[(.*?)\]\{([\s\S]*?)\}"
        md.inlinePatterns.register(markdown_custom_block_style_text(CUSTOM_BLOCK_STYLE_PATTERN,md),"custom_block_style",175)

        LINK_PATTERN = r'(?<!\!)\b(?:https?|http|ftp|sftp):\/\/[-A-Za-z0-9+&@#\/%?=~_|!:,.;]*[-A-Za-z0-9+&@#\/%=~_|]'
        md.inlinePatterns.register(markdown_url_processor(LINK_PATTERN,md),"embedded_link", 175)

class markdown_image_mixin(InlineProcessor):
    def __init__(self,pattern,md,images):
        super().__init__(pattern,md)
        self.images = images

    def handleMatch(self,m,data):
        el = etree.Element("img")
        el.set("src",m.group(2))
        el.set("alt",m.group(1))

        if os.path.normpath(m.group(2)) in self.images:
            el.set("onclick", f"open_image_viewer(\"{m.group(2)}\",true)")

        if m.group(3):
            title = m.group(3).strip(' "')
            el.set("title", title)

        return el,m.start(0),m.end(0)

class markdown_mixin_extension(Extension):
    def __init__(self,local_image_checklist):
        super().__init__()

        self.gallery_image_paths = local_image_checklist

    def extendMarkdown(self,md):
        md.inlinePatterns.register(
            markdown_image_mixin(r'!\[([^\]]*)]\(([^"\)]+)(\s"([^"]*)")?\)',md,self.gallery_image_paths),"custom_image_link",176
        )

def check_file_exists(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    return True

def check_folder_exists(folder_path):
    if not os.path.exists(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        return False
    return True

def remove_base_dir(index, path):
    base_dir = index["base_directory"]
    if path.startswith(base_dir):
        return path[len(base_dir) + len(os.sep)-1:].lstrip(os.sep)
    else:
        return path

def config_get_default(config,parent_config,group,value,*default):
    if config.has_option(group,value):
        return config.get(group,value)
    elif hasattr(parent_config,"has_option") and parent_config.has_option(group,value):
        return parent_config.get(group,value)
    elif default:
        return default[0]
    else:
        raise ValueError(f"Default value not provided for {group}.{value}")


def config_get_section(config, section):
    if config.has_section(section):
        return dict(config.items(section))
    else:
        return {}

def read_config(config_path,*parent_config_path):
    print("Reading configuration...")
    config        = configparser.ConfigParser()
    parent_config = configparser.ConfigParser()

    config.read(config_path)
    if parent_config_path[0]:
        if os.path.exists(parent_config_path[0]):
            parent_config.read(parent_config_path[0])
            print(f"Parent config file {parent_config_path[0]} found and loaded.")
        else:
            print(f"Parent config file {parent_config_path[0]} not found.")

    settings = {
        "title":        config_get_default(config,parent_config,"Settings","title","Gallery title!"),
        "image_folder": config_get_default(config,parent_config,"Settings","image_folder","pictures"),
        "page_title":   config_get_default(config,parent_config,"Settings","page_title",config_get_default(config,parent_config,"Settings","title","Gallery title!")),
    }

    embed = {
        "enabled"    : config_get_default(config,parent_config,"Embed","enabled","false") == "true",
        "title"      : config_get_default(config,parent_config,"Embed","title","An image gallery"),
        "description": config_get_default(config,parent_config,"Embed","description","A very filled image gallery with images"),
        "image"      : config_get_default(config,parent_config,"Embed","image","https://github.com/9551-Dev.png"),
        "color"      : config_get_default(config,parent_config,"Embed","color","#90f91f"),
        "url"        : config_get_default(config,parent_config,"Embed","url","https://github.com/9551-Dev")
    }

    index = {
        "index_style":     config_get_default(config,parent_config,"Index","page","assets/index_template.html"),
        "enabled":         config_get_default(config,parent_config,"Index","enabled","true") == "true",
        "base_directory":  config_get_default(config,parent_config,"Index","base_directory","docs"),
        "base_index_name": config_get_default(config,parent_config,"Index","base_index_name","index.html"),

        "generate_project_index":      config_get_default(config,parent_config,"Index.special_rules","generate_project_index","false"),
        "generate_project_root_index": config_get_default(config,parent_config,"Index.special_rules","generate_project_root_index","false"),
        "project_index_name":          config_get_default(config,parent_config,"Index.special_rules","project_index_name","index.html"),
        "project_root_index_name":     config_get_default(config,parent_config,"Index.special_rules","project_root_index_name","dir.html"),

        "root_index_name":  config_get_default(config,parent_config,"Index.special_rules","root_index_name","root_index.html"),
        "root_index_super": config_get_default(config,parent_config,"Index.special_rules","root_index_super","UNUSED"),
    }

    core = {
        "template_path": config_get_default(config,parent_config,"Core","template_path"),
        "css_path":      config_get_default(config,parent_config,"Core","css_path"),
        "js_path":       config_get_default(config,parent_config,"Core","js_path")
    }

    output = {
        "output_folder":         config_get_default(config,parent_config,"Output","output_folder","PLS_CONFIGURE_THX_:3"),
        "images_directory_name": config_get_default(config,parent_config,"Output","images_directory_name","images"),
        "core_directory_name":   config_get_default(config,parent_config,"Output","core_directory_name","core"),
        "output_file_name":      config_get_default(config,parent_config,"Output","output_file_name","index.html")
    }

    pagefile = {
        "enabled":           config_get_default(config,parent_config,"Pagefile","enabled","false") == "true",
        "source_file":       config_get_default(config,parent_config,"Pagefile","source","NONE"),
        "image_descriptors": config_get_section(config,"Pagefile.descriptions")
    }

    required_files = [settings['image_folder'], core['template_path'], core['css_path'], core['js_path']]
    for file_path in required_files:
        if not check_file_exists(file_path):
            print("Exiting: One or more required files not found.")
            exit(1)

    print("Configuration read successfully.")
    return settings,core,output,index,embed,pagefile

def attach_pagefile(content,output,local_image_checklist,pagefile):
    if os.path.exists(pagefile["source_file"]):
        with open(pagefile["source_file"], 'r') as page_data:
            markdown_data = page_data.read()
            print("\nPage text file loaded successfully.")
    else:
        print("Page file does not exist.")
        return content

    print("Generating HTML from markdown and applying macros")

    markdown_data = markdown_data.replace("__IMAGE__",os.path.join("./",output["images_directory_name"]))

    generated_markdown = markdown.markdown(markdown_data,
        extensions = [
            "markdown.extensions.extra",
            "markdown.extensions.legacy_attrs",
            "markdown.extensions.admonition",
            "markdown.extensions.legacy_em",
            "markdown.extensions.meta",
            "markdown.extensions.smarty",
            "markdown.extensions.codehilite",
            epic_markdown_extension(),
            markdown_mixin_extension(local_image_checklist)
        ]
    )

    content = content.replace("{{markdown}}",generated_markdown)
    print("Markdown content attached.")

    return content

def set_comment(content,state,comment_type):
    content = content.replace(f"{{{{{comment_type}_start}}}}", "<!--" if state else "")
    content = content.replace(f"{{{{{comment_type}_end}}}}",   "-->"  if state else "")

    return content

def get_image_filenames(image_folder):
    image_files = []
    for root, dirs, files in os.walk(image_folder):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_files.append(os.path.join(root, file))
    return image_files

def generate_html(settings, core, output, embed, pagefile):
    print("\nGenerating HTML...")
    with open(core['template_path'], 'r') as template_file:
        template_content = template_file.read()
    with open(core['js_path'], 'r') as js_file:
        js_content = js_file.read()
    with open(core['css_path'], 'r') as css_file:
        css_content = css_file.read()

    # get all recursive mages in image_folder
    image_files = get_image_filenames(settings['image_folder'])
    image_groups = {}
    for image_file in image_files:
        directory = os.path.dirname(image_file)
        if directory not in image_groups:
            image_groups[directory] = []
            print("Found image group " + directory)

        image_groups[directory].append(image_file)

    output_images_folder = os.path.join(output['output_folder'], output['images_directory_name'])
    os.makedirs(output_images_folder, exist_ok=True)
    print("output images folder: " + output_images_folder)

    # What the fuck is happening here oh my god i hated implementing groups, this is a clusterfuck
    for group, images in image_groups.items():
        if group != settings['image_folder']:
            group_name = os.path.basename(group)
        else:
            group_name = ""

        print(f"Creating image group: {group_name}")

        for image_file in images:

            # like actually kill me already
            relative_path = os.path.relpath(image_file,start=settings['image_folder'])
            output_folder = os.path.join(output_images_folder, os.path.dirname(relative_path))
            os.makedirs(output_folder, exist_ok=True)

            output_image_file = os.path.join(output_folder, os.path.basename(image_file))

            print(f"Copying image: {image_file} to {output_image_file}")

            shutil.copy2(image_file, output_image_file)

    image_tags = ""
    make_header = None
    for group, images in image_groups.items():
        make_header = group != settings['image_folder']
        if make_header:
            group_name = os.path.basename(group)
        else:
            group_name = ""

        # cancer juice
        relative_path = os.path.relpath(group,start=settings['image_folder'])

        copied_image_paths = [os.path.join(output["images_directory_name"], relative_path, os.path.basename(path)) for path in images]
        group_image_tags = '\n'.join([f'            <img src="{path}" alt="{os.path.basename(path)}" onclick="open_image_viewer(\'{path}\')">'
                                    for path in copied_image_paths])

        if make_header:
            image_tags += f"<h2 class='image-group-header'>{group_name}</h2>\n" + group_image_tags
        else:
            image_tags += group_image_tags


    template_content = set_comment(template_content,not embed["enabled"],"embed_enable")

    template_content = template_content.replace("{{page_title}}", settings["page_title"])
    template_content = template_content.replace("{{title}}", settings["title"])
    template_content = template_content.replace("{{css_path}}", os.path.join(output["core_directory_name"], os.path.basename(core["css_path"])))
    template_content = template_content.replace("{{js_path}}",  os.path.join(output["core_directory_name"], os.path.basename(core["js_path"])))
    template_content = template_content.replace("{{image_tags}}", image_tags)

    template_content = template_content.replace("{{embed_title}}",       embed["title"])
    template_content = template_content.replace("{{embed_description}}", embed["description"])
    template_content = template_content.replace("{{embed_url}}",         embed["url"])
    template_content = template_content.replace("{{embed_image}}",       embed["image"])
    template_content = template_content.replace("{{embed_color}}",       embed["color"])

    if pagefile["enabled"]:
        local_image_checklist = [
            os.path.join(output["images_directory_name"],"" if group == settings["image_folder"] else os.path.basename(group),os.path.basename(path))
            for group, images in image_groups.items()
            for path in images
            # Man wtf
            if (
                True if group != settings["image_folder"] else True # make root group not have a group name
            )
        ]

        template_content = attach_pagefile(template_content,output,local_image_checklist,pagefile)
        template_content = template_content.replace("{{markdown_container_properties}}","")
    else:
        template_content = template_content.replace("{{markdown}}","")
        template_content = template_content.replace("{{markdown_container_properties}}","style='display: none;'")


    image_paths_js = ",\n    ".join([
        f'"{os.path.join(output["images_directory_name"], "" if group == settings["image_folder"] else os.path.relpath(group, start=settings["image_folder"]), os.path.basename(path))}"'
        for group, images in image_groups.items()
        for path in images
    ])

    js_content = js_content.replace('{{image_paths}}', image_paths_js)

    output_core_folder = os.path.join(output['output_folder'], output['core_directory_name'])
    os.makedirs(output_core_folder, exist_ok=True)

    output_js_path = os.path.join(output_core_folder, os.path.basename(core['js_path']))
    with open(output_js_path, 'w') as output_js_file:
        output_js_file.write(js_content)

    output_css_path = os.path.join(output_core_folder, os.path.basename(core['css_path']))
    with open(output_css_path, 'w') as output_css_file:
        output_css_file.write(css_content)

    output_file_path = os.path.join(output['output_folder'], output['output_file_name'])
    with open(output_file_path, 'w') as output_file:
        output_file.write(template_content)

    print(f'\nGenerated {output_file_path} successfully.')

def get_index_content(index):
    if index['index_style']:
        if os.path.exists(index['index_style']):
            with open(index['index_style'], 'r') as index_file:
                return index_file.read()
        else:
            print(f"Error: Index HTML file not found at {index['index_style']}.")
    return None

def generate_directory_index(directory_path,index,index_name):
    print(f"Generating index for directory: {directory_path}")

    index_content = get_index_content(index)
    if index_content:

        index_content = index_content.replace('{{title}}',f"Index of <span style='font-size:50px;color:DodgerBlue'>/{remove_base_dir(index,directory_path)}</span>")
        index_content = index_content.replace('{{header}}',remove_base_dir(index,directory_path))

        directory_list_content = ""

        directory_items = []
        file_items = []

        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                directory_items.append(item)
            else:
                if item != index_name:
                    file_items.append(item)

        directory_items.sort()
        file_items     .sort()

        for item in directory_items:
            directory_list_content += f"        <li><a class='index_directory' href=\"{item}/\">{item}/ <sub>[DIR]</sub></a></li>\n"
        for item in file_items:
            directory_list_content += f"        <li><a class='index_file' href=\"{item}\">{item} <sub>[FILE]</sub></a></li>\n"

        directory_list_content += f"        <li><a class='index_self' href=\"{index_name}\">{index_name} <sub>[THIS]</sub></a></li>\n"

        index_content = index_content.replace('{{directory_list}}',directory_list_content)

        if os.path.normpath(directory_path) == os.path.normpath(index["base_directory"]):
            index_content = set_comment(index_content,True,"comment")
        elif os.path.dirname(remove_base_dir(index,directory_path)) == "":
            index_content = index_content.replace('{{parent}}',"")
            index_content = set_comment(index_content,False,"comment")
        elif (directory_path.split(os.sep)[0] == index["base_directory"]) and (os.path.normpath(directory_path) != os.path.normpath(index["base_directory"])):
            index_content = index_content.replace('{{parent}}',f"/{os.path.dirname(remove_base_dir(index,directory_path))}/")
            index_content = set_comment(index_content,False,"comment")
        else:
            index_content = index_content.replace('{{parent}}',f"{os.path.dirname(directory_path)}")
            index_content = set_comment(index_content,False,"comment")

        with open(os.path.join(directory_path,index_name), 'w') as index_file:
            index_file.write(index_content)
    else:
        print("Error: Index content not found.")

def generate_directory_indexes(output_folder,output,index):
    print(f"\nGenerating directory indexes for: {output_folder}")

    output_dirs = output_folder.split(os.path.sep)
    directory_paths = []

    for i in range(len(output_dirs)):
        directory_path = os.path.join(*output_dirs[:i+1])
        directory_paths.append(directory_path)

    match_at = 0
    for i in range(len(directory_paths)):
        if os.path.normpath(directory_paths[i]) == os.path.normpath(index["base_directory"]):
            match_at = i


    for i in range(match_at+1,len(directory_paths)):
        directory_path = directory_paths[i]
        if directory_path != output_folder:
            generate_directory_index(directory_path,index,index["base_index_name"])

    if index["generate_project_index"]:
        print(f"\nGenerating project directory indexes for: {directory_path}")

        if index["generate_project_root_index"]:
            generate_directory_index(directory_path,index,index["project_root_index_name"])

        for root,dirs,files in os.walk(directory_path):
            for dir_name in dirs:
                current_dir = os.path.join(root, dir_name)
                generate_directory_index(current_dir,index,index["project_index_name"])

    generate_directory_index(index["base_directory"] or output["output_folder"].split(os.sep)[0],index,index["root_index_name"] or "index.html")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py <config_path/parent_config_path> [config_path_sub]")
        exit(1)

    parent_config_path = None
    config_path        = sys.argv[1]

    if len(sys.argv) >= 3:
        parent_config_path = sys.argv[1]
        config_path        = sys.argv[2]

    settings,core,output,index,embed,pagefile = read_config(config_path,parent_config_path)

    print(f'\nTitle: {settings["page_title"]}')
    print(f'Index files: {index["enabled"] and "enabled" or "disabled"} ({index["enabled"]})')
    print(f'Markdown pagefile: {pagefile["enabled"] and "enabled" or "disabled"} ({pagefile["enabled"]})')

    generate_html(settings,core,output,embed,pagefile)

    if index["enabled"]:
        generate_directory_indexes(output['output_folder'], output, index)