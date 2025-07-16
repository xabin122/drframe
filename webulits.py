import os
import re

TEMPLATES_DIR = "templates"

def eval_condition(expr, context):
    try:
        return bool(eval(expr, {}, context))
    except Exception:
        return False

def parse_blocks(template):
    # پشتیبانی از if/elif/else/endif, block/endblock, for/endfor
    pattern = r"{%\s*(if|elif|else|endif|block|endblock|for|endfor)(?:\s+(.*?))?\s*%}"
    return [(m.group(1), m.group(2) or '', m.start(), m.end()) for m in re.finditer(pattern, template)]

def render_section(template, context):
    out = []
    pos = 0
    tokens = parse_blocks(template)
    idx = 0

    while idx < len(tokens):
        tag, expr, start, end = tokens[idx]

        if tag == 'if':
            out.append(template[pos:start])
            nest = 1
            j = idx + 1
            while j < len(tokens):
                if tokens[j][0] == 'if':
                    nest += 1
                elif tokens[j][0] == 'endif':
                    nest -= 1
                    if nest == 0:
                        break
                j += 1
            if j >= len(tokens):
                block_inside = template[end:]
                pos = len(template)
                idx = j
            else:
                block_inside = template[end:tokens[j][2]]
                pos = tokens[j][3]
                idx = j

            branches = []
            branch_conditions = []
            last_block_pos = 0
            matches = list(re.finditer(r"{%\s*(elif|else)(.*?)%}", block_inside))

            if matches:
                for i, m in enumerate(matches):
                    branches.append(block_inside[last_block_pos:m.start()])
                    prev_tag = 'if' if i == 0 else matches[i - 1].group(1)
                    prev_expr = expr if i == 0 else matches[i - 1].group(2).strip()
                    branch_conditions.append((prev_tag, prev_expr))
                    last_block_pos = m.end()
                branches.append(block_inside[last_block_pos:])
                branch_conditions.append((matches[-1].group(1), matches[-1].group(2).strip()))
            else:
                branches.append(block_inside)
                branch_conditions.append(('if', expr))

            rendered_branch = ''
            for typ, cond in branch_conditions:
                if typ in ['if', 'elif'] and eval_condition(cond, context):
                    rendered_branch = render_section(branches[branch_conditions.index((typ, cond))], context)
                    break
                elif typ == 'else' and not rendered_branch:
                    rendered_branch = render_section(branches[branch_conditions.index((typ, cond))], context)
                    break
            out.append(rendered_branch)

        elif tag == 'for':
            out.append(template[pos:start])
            nest = 1
            j = idx + 1
            while j < len(tokens):
                if tokens[j][0] == 'for':
                    nest += 1
                elif tokens[j][0] == 'endfor':
                    nest -= 1
                    if nest == 0:
                        break
                j += 1
            if j >= len(tokens):
                print("🟠[Template Warning]: unmatched {% for %} with no {% endfor %}")
                block_inside = template[end:]
                pos = len(template)
                idx = j
            else:
                block_inside = template[end:tokens[j][2]]
                pos = tokens[j][3]
                idx = j

            # expr باید با این الگو باشه: var in iterable
            m = re.match(r'([\w_]+)\s+in\s+([.\w_]+)', expr.strip())
            if m:
                loop_var, loop_in = m.group(1), m.group(2)
                iterable = context
                for part in loop_in.split('.'):
                    if isinstance(iterable, dict) and part in iterable:
                        iterable = iterable[part]
                    else:
                        iterable = []
                        break
                # اگر چیزی قابل تکرار پیدا شد:
                if iterable and hasattr(iterable, '__iter__'):
                    forloop_ctx = dict(context)
                    for i, item in enumerate(iterable):
                        forloop_ctx[loop_var] = item
                        # قالب‌بندی forloop شبیه جنگو
                        forloop_ctx['forloop'] = {
                            'counter': i+1, 'counter0': i, 'first': i==0, 'last': i==(len(iterable)-1)
                        }
                        out.append(render_section(block_inside, forloop_ctx))
            else:
                # اگر سینتکس اشتباه
                out.append(block_inside)
        elif tag == 'block':
            out.append(template[pos:start])
            nest = 1
            j = idx + 1
            while j < len(tokens):
                if tokens[j][0] == 'block':
                    nest += 1
                elif tokens[j][0] == 'endblock':
                    nest -= 1
                    if nest == 0:
                        break
                j += 1
            if j >= len(tokens):
                print(f"🟠[Template Warning] : unmatched {{% block {expr.strip()} %}} with no {{% endblock %}} found.")
                pos = len(template)
                idx = j
            else:
                blockname = expr.strip()
                out.append("{{__BLOCK__:%s}}" % blockname)
                pos = tokens[j][3]
                idx = j
        else:
            idx += 1
            continue
        idx += 1
    out.append(template[pos:])

    # ------ بخش جایگزینی متغیرها با پشتیبانی از دات‌نتیشن -------
    def repl_var(m):
        key = m.group(1).strip()
        value = context
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                value = ""
                break
        return str(value)
    return re.sub(r"\{\{\s*([.\w]+)\s*\}\}", repl_var, ''.join(out))

def extract_blocks(template):
    blocks = {}
    pattern = r"{%\s*block\s+(\w+)\s*%}([\s\S]*?){%\s*endblock\s*%}"
    for m in re.finditer(pattern, template):
        blocks[m.group(1)] = m.group(2)
    return blocks

def replace_blocks(base, blocks):
    def repl(m):
        name = m.group(1)
        return blocks.get(name, m.group(0))
    return re.sub(r"\{\{__BLOCK__:(\w+)\}\}", repl, base)

def render(template_name, context=None):
    if context is None:
        context = {}
    path = os.path.join(TEMPLATES_DIR, template_name)
    with open(path, encoding="utf-8") as f:
        tpl = f.read()

    extend_m = re.search(r"{%\s*extends\s*['\"]([^'\"]+)['\"]\s*%}", tpl)
    if extend_m:
        tpl = re.sub(r"{%\s*extends\s*['\"]([^'\"]+)['\"]\s*%}", "", tpl)
        blocks = extract_blocks(tpl)
        base_path = os.path.join(TEMPLATES_DIR, extend_m.group(1))
        with open(base_path, encoding="utf-8") as bf:
            base = bf.read()
        base_rendered = render_section(base, context)
        merged = replace_blocks(base_rendered, blocks)
        return render_section(merged, context)
    else:
        return render_section(tpl, context)

def serve_static(handler, path, static_dir="static"):
    from urllib.parse import unquote
    file_path = unquote(path.lstrip("/"))
    full_path = os.path.join(os.getcwd(), file_path)
    if os.path.isfile(full_path):
        handler.send_response(200)
        if file_path.endswith(".css"):
            handler.send_header('Content-Type', 'text/css')
        elif file_path.endswith(".js"):
            handler.send_header('Content-Type', 'application/javascript')
        elif file_path.endswith((".jpg", ".jpeg")):
            handler.send_header('Content-Type', 'image/jpeg')
        elif file_path.endswith(".png"):
            handler.send_header('Content-Type', 'image/png')
        elif file_path.endswith(".pdf"):
            handler.send_header('Content-Type', 'application/pdf')
        else:
            handler.send_header('Content-Type', 'application/octet-stream')
        handler.end_headers()
        with open(full_path, "rb") as f:
            handler.wfile.write(f.read())
    else:
        handler.send_error(404, "Static file not found")
