import os, re
from github import Auth
from github import Github, GithubIntegration
from tree_sitter import Language, Parser

from groq import Groq

client = Groq(api_key=os.environ['GROQ_API_KEY'],)

def authenticate_github(app_id: int, installation_id, private_key: str):
    gi = GithubIntegration(integration_id=app_id, private_key=private_key)
    g = gi.get_github_for_installation(installation_id)
    return g

def get_pull_request(g, repo_name: str, pr_number: int):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return pr

def parse_changed_lines(patch: str):
    added_or_modified_lines = set()
    deleted_lines = set()
    for line in patch.splitlines():
        if line.startswith("@@"):
            match = re.findall(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                old_start, old_count, new_start, new_count = match[0]

                old_start = int(old_start)
                old_count = int(old_count or 1)
                for l in range(old_start, old_start + old_count):
                    deleted_lines.add(l)

                new_start = int(new_start)
                new_count = int(new_count or 1)
                for l in range(new_start, new_start + new_count):
                    added_or_modified_lines.add(l)

    return {
        "added_or_modified_lines": added_or_modified_lines,
        "deleted_lines": deleted_lines
    }

def get_file_contents(g, repo_name: str, file_path: str, commit_sha: str):
    repo = g.get_repo(repo_name)
    contents = repo.get_contents(file_path, ref=commit_sha)
    return contents.decoded_content.decode()

def get_lines_changed(pr):
    files = pr.get_files()
    file_changes = {}
    for file in files:
        if file.status == "removed":
            continue
        file_changes[file.filename] = parse_changed_lines(file.patch)

    return file_changes

def get_paraser(language_name):
    Language.build_library(
        'my-languages.so',
        [
            './tree-sitter-python',
            './tree-sitter-javascript',
            './tree-sitter-cpp'
        ]
    )

    PY_LANGUAGE = Language('my-languages.so', 'python')
    JS_LANGUAGE = Language('my-languages.so', 'javascript')
    CPP_LANGUAGE = Language('my-languages.so', 'cpp')

    LANGUAGES = {
        'python': PY_LANGUAGE,
        'javascript': JS_LANGUAGE,
        'cpp': CPP_LANGUAGE,
    }
    parser = Parser()
    parser.set_language(LANGUAGES[language_name])
    return parser

def extract_functions(code, language_name, changed_lines):
    parser = get_paraser(language_name)
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    functions = []

    def node_within_lines(node):
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        return any([start_line <= line <= end_line for line in changed_lines])
    
    def traverse(node):
        if language_name == "python" and node.type == "function_definition":
            if node_within_lines(node):
                functions.append(node.text.decode())
        elif language_name == 'javascript' and node.type in ['function_declaration', 'method_definition', 'arrow_function']:
            if node_within_lines(node):
                functions.append(node.text.decode())
        elif language_name == 'cpp' and node.type in ['function_definition']:
            if node_within_lines(node):
                functions.append(node.text.decode())

        for child in node.children:
            traverse(child)

    traverse(root_node)
    return functions




if __name__ == "__main__":
    # chat_completion = client.chat.completions.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": "Expalin the difference between a list and a tuple",
    #         }
    #     ],
    #     model="deepseek-r1-distill-qwen-32b"
    # )

    # print(chat_completion.choices[0].message.content)
    with open("/Applications/Development/iNTUition_AIcoholics/backend/pulloutrequest.2025-03-22.private-key.pem", "r") as f:
        private_key = f.read()

    g = authenticate_github(1188098, 63112022, private_key=private_key)
    print(g.get_repo("raghavg332/Testing").name)
    pr = get_pull_request(g, "raghavg332/Testing", 5)
    print(pr.title)
    print(pr)
    lines_changed = get_lines_changed(pr)
    print(lines_changed)
    code = get_file_contents(g, "raghavg332/Testing", list(lines_changed.keys())[0], pr.head.sha)
    print(code)
    functions = extract_functions(code, "python", lines_changed[list(lines_changed.keys())[0]]['added_or_modified_lines'])
    print(functions)