// URL: https://observablehq.com/d/8ed172ec5b1d17d2
// Title: API Documentation
// Author: Sébastien Pierre (@sebastien)
// Version: 230
// Runtime version: 1

const m0 = {
  id: "8ed172ec5b1d17d2@230",
  variables: [
    {
      inputs: ["md"],
      value: (function(md){return(
md`# API Documentation`
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`This notebook defines primitives to document APIs within Observable directly.`
)})
    },
    {
      inputs: ["Docs"],
      value: (function(Docs){return(
Docs()
)})
    },
    {
      name: "Docs",
      inputs: ["docs","html","map","docFunction","dom"],
      value: (function(docs,html,map,docFunction,dom){return(
(collection = docs) => {
  const preview = html.div("preview");
  const previews = map(collection, ({ definition }) => docFunction(definition));
  const onFunctionSelect = (event) => {
    const fun = event.target.name;
    dom.set(preview, previews[fun]);
  };
  const functions = html.form(
    { multiple: "" },
    Object.entries(collection).map(([k, v]) =>
      html.div(
        { _: "doc-selector" },
        html.input({
          type: "checkbox",
          id: k,
          name: k,
          onInput: onFunctionSelect
        }),
        html.label({ for: k }, k)
      )
    )
  );
  return html.div(
    {
      style: {
        display: "grid",
        gridTemplateColumns: "160px max-content"
      }
    },
    html.div(functions),
    preview
  );
}
)})
    },
    {
      inputs: ["doc"],
      value: (function(doc){return(
doc(
  {
    name: "doc",
    desc: "Documents JavaScript values, including functions and objects",
    args: {
      name: "The name of the function.",
      desc: "The description of the function."
    }
  },
  doc
)
)})
    },
    {
      name: "docs",
      value: (function(){return(
{}
)})
    },
    {
      name: "doc",
      inputs: ["docs","docFunction"],
      value: (function(docs,docFunction){return(
(definition, functor, collection = docs) => {
  const name = (functor ? functor.name : null) || definition.name || "function";
  if (collection[name] === undefined) {
    collection[name] = { definition, implementation: functor };
  }
  return docFunction(definition);
}
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Supporting Functions`
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`### Function Argument`
)})
    },
    {
      inputs: ["docArgument"],
      value: (function(docArgument){return(
docArgument("name", "The name of the function.")
)})
    },
    {
      name: "docArgument",
      inputs: ["html"],
      value: (function(html){return(
(name, def) => html.div(html.dt(name), html.dd(def))
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`### Function Prototype`
)})
    },
    {
      inputs: ["docPrototype"],
      value: (function(docPrototype){return(
docPrototype({
  name: "map",
  args: { collection: "Collection of items", functor: "Function to invoke" }
})
)})
    },
    {
      name: "docPrototype",
      inputs: ["html"],
      value: (function(html){return(
({ name, args }) => {
  const args_html = Object.entries(args || {}).reduce(
    (r, [k, v], i) =>
      r.concat([
        i === 0 ? null : html.span({ _: "api-sep" }, ", "),
        html.span({ _: "api-doc-name api-is-argument", title: v }, k)
      ]),
    []
  );
  return html.div(
    { _: "api-doc-proto" },
    html.span({ _: "api-doc-proto-name" }, "📖 ", name || typeof name),
    html.span({ _: "api-doc-proto-args" }, "(", args_html, ")")
  );
}
)})
    },
    {
      name: "docFunction",
      inputs: ["md","html","docPrototype"],
      value: (function(md,html,docPrototype){return(
(definition) => {
  const name = definition.name;
  const desc = md`${definition.desc}`;
  return html.div(
    { _: "api-doc-root" },
    html.div(
      { _: "api-doc" },
      html.div({ _: "api-doc-header" }, docPrototype(definition)),
      html.div(
        { _: "api-doc-body" },
        desc,
        definition.args
          ? html.dl(
              { _: "api-doc-args" },
              Object.entries(definition.args).reduce(
                (r, [name, text]) =>
                  r.concat([
                    html.dt({ _: "api-doc-args-name" }, name),
                    html.dd({ _: "api-doc-args-desc" }, text)
                  ]),
                []
              )
            )
          : null
      )
    )
  );
}
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Styling`
)})
    },
    {
      name: "Stylesheet",
      inputs: ["stylesheet"],
      value: (function(stylesheet){return(
stylesheet({
  ".api-doc-root": {
    display: "block",
    "max-width": "43em",
    "font-family": "var(--sans-serif)",
    "font-size": "14px"
  },
  ".api-doc": {
    border: "1px solid #f9f5e1",
    "border-radius": "8px",
    "box-sizing": "border-box",
    "box-shadow": "2px 2px 2px rgba(119,110,69,0.15)",

    display: "block"
  },
  ".api-doc-header": {
    "background-color": "#fff1ab",
    padding: "16px",
    "font-weight": "bold"
  },
  ".api-doc-proto": { "font-family": "var(--monospace)" },
  ".api-doc-args": {
    padding: "16px",
    margin: "0px",
    "background-color": "#FAFAFA"
  },

  ".api-doc-args-name": {
    "font-family": "var(--monospace)",
    "font-weight": "bold",
    "margin-top": "1px"
  },
  ".api-doc-args-desc": { "font-family": "var(--serif)" },

  ".api-doc-body": {
    "font-family": "var(--serif)",
    padding: "0px 16px"
  }
})
)})
    },
    {
      from: "@sebastien/boilerplate",
      name: "stylesheet",
      remote: "stylesheet"
    },
    {
      from: "@sebastien/boilerplate",
      name: "html",
      remote: "html"
    },
    {
      from: "@sebastien/boilerplate",
      name: "dom",
      remote: "dom"
    },
    {
      from: "@sebastien/boilerplate",
      name: "map",
      remote: "map"
    }
  ]
};

const m1 = {
  id: "@sebastien/boilerplate",
  variables: [
    {
      name: "stylesheet",
      inputs: ["html","each","maptype","str","until"],
      value: (function(html,each,maptype,str,until){return(
(rules, name = "default", waitForAvailability = true) => {
  const id = `stylesheet-${name || "default"}`;
  const existing = document.getElementById(id);
  const node = existing || html.style({ id, name });
  const updater = () => {
    const sheet = node.sheet;
    if (!sheet) {
      return false;
    }
    while (sheet && sheet.cssRules && sheet.cssRules.length) {
      sheet.deleteRule(0);
    }
    Object.entries(rules).forEach(([k, v]) => {
      // We support {@:[...]} for imports and such
      if (k === "@") {
        each(v, (_) => sheet.insertRule(`${v};`, 0));
      } else {
        const w = maptype(v, {
          object: (_) =>
            Object.entries(_)
              .map(([k, v]) => `${k}: ${v};`)
              .join("\n"),
          array: (_) => _.join("\n"),
          _: str
        });
        sheet.insertRule(`${k} {${w}}`, 0);
      }
    }, sheet);
    return true;
  };
  // In Observable, the node will only be mounted at a later point, and we need
  // to test for the sheet and cssRules properties to be set before actually doing
  // the update. In other environments, we can just proceed with the update already.
  !updater() &&
    waitForAvailability &&
    until(
      () => {
        return node.sheet && node.sheet.cssRules;
      },
      updater,
      100,
      10
    );
  return node;
}
)})
    },
    {
      name: "html",
      inputs: ["dom"],
      value: (function(dom){return(
(function () {
  const { create } = dom;
  return [
    "a",
    "abbr",
    "acronym",
    "address",
    "applet",
    "area",
    "article",
    "aside",
    "audio",
    "b",
    "base",
    "basefont",
    "bdo",
    "big",
    "blockquote",
    "body",
    "br",
    "button",
    "canvas",
    "caption",
    "center",
    "cite",
    "code",
    "col",
    "colgroup",
    "command",
    "datalist",
    "dd",
    "del",
    "details",
    "dfn",
    "dir",
    "div",
    "dl",
    "dt",
    "em",
    "embed",
    "fieldset",
    "figcaption",
    "figure",
    "font",
    "footer",
    "form",
    "frame",
    "frameset",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hgroup",
    "hr",
    "html",
    "i",
    "iframe",
    "img",
    "input",
    "ins",
    "isindex",
    "kbd",
    "keygen",
    "label",
    "legend",
    "li",
    "link",
    "map",
    "mark",
    "menu",
    "meta",
    "meter",
    "nav",
    "noframes",
    "noscript",
    "object",
    "ol",
    "optgroup",
    "option",
    "output",
    "p",
    "param",
    "pre",
    "progress",
    "q",
    "rp",
    "rt",
    "ruby",
    "s",
    "samp",
    "script",
    "section",
    "select",
    "slot",
    "small",
    "source",
    "span",
    "strike",
    "strong",
    "style",
    "sub",
    "summary",
    "sup",
    "table",
    "tbody",
    "td",
    "textarea",
    "template",
    "tfoot",
    "th",
    "thead",
    "time",
    "title",
    "tr",
    "tt",
    "u",
    "ul",
    "video",
    "wbr",
    "xmp"
  ].reduce(
    (r, k) => {
      r[k] = (...args) => create(k, args);
      return r;
    },
    { ...dom }
  );
})()
)})
    },
    {
      name: "dom",
      inputs: ["setattr","each","list"],
      value: (function(setattr,each,list){return(
(() => {
  const namespaces = {
    svg: "http://www.w3.org/2000/svg",
    xlink: "http://www.w3.org/1999/xlink"
  };
  const append = (node, value) => {
    const type = typeof value;
    if (value == undefined) {
      return;
    } else if (type === "string") {
      node.appendChild(document.createTextNode(value));
    } else if (type === "object" && value.nodeType !== undefined) {
      node.appendChild(value);
    } else if (type === "object" && value instanceof Array) {
      for (let j = 0; j < value.length; j++) {
        append(node, value[j]);
      }
    } else {
      var has_properties = false;
      for (let k in value) {
        let ns = null;
        let dot = k.lastIndexOf(":");
        let v = value[k];
        // We skip undefined properties
        if (v !== undefined) {
          if (dot >= 0) {
            ns = k.substr(0, dot);
            ns = namespaces[ns] || ns;
            k = k.substr(dot + 1, k.length);
          }
          if (k == "_" || k == "_class" || k == "klass") {
            k = "class";
          }
          // We leverage the `setattr` function that manages setting the attributes
          // easily.
          if (ns) {
            setattr(node, k, v, 0, ns);
          } else if (k.startsWith("on") && node[k] !== undefined) {
            // Event handlers like "onclick" cannot be set through the setAttribute method,
            // but have to be set explicitely.
            node[k] = v;
          } else {
            setattr(node, k, v);
          }
          has_properties = true;
        }
      }
      if (!has_properties) {
        node.appendChild(document.createTextNode("" + value));
      }
    }
    return node;
  };

  const clear = (node) => {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
    return node;
  };

  const set = (node, ...content) => append(clear(node), ...content);
  const replace = (node, ...content) => {
    var not_found = true;
    node.parentNode &&
      content.forEach((_) => {
        if (_ === node) {
          not_found = false;
        }
        if (node.parentNode) {
          node.parentNode.insertBefore(_, node);
        }
      });
    not_found && node.parentNode && node.removeChild(node);
    return content;
  };
  const unmount = (_) => {
    _ && _.parentNode && _.parentNode.removeChild(_);
    return _;
  };
  const remount = (node, current, previous) => {
    const parent = node.parentNode;
    each(list(previous), unmount);
    each(list(current), parent ? (_) => parent.insertBefore(_, node) : unmount);
    return current;
  };
  const create = (name, args) => {
    const node = document.createElement(name);
    for (var i = 0; i < args.length; i++) {
      append(node, args[i]);
    }
    return node;
  };
  const createns = (ns, name, args) => {
    const node = document.createElementNS(ns, name);
    for (var i = 0; i < args.length; i++) {
      append(node, args[i]);
    }
    return node;
  };
  return {
    namespaces,
    create,
    createns,
    set,
    append,
    clear,
    replace,
    unmount,
    remount
  };
})()
)})
    },
    {
      name: "map",
      inputs: ["idem","type","empty","iter"],
      value: (function(idem,type,empty,iter){return(
(collection,processor=idem) => {
  const t = type(collection);
  const e = empty(collection);
  return iter(collection, 
       t === "string"
       ? (v,i,r) => {r.push(processor(v,i,collection));return r}
       : t === "list" 
       ? (v,i,r) => {r.push(processor(v,i,collection));return r}
       : (v,k,r) => {r[k]=processor(v,k,collection);return r},
       t === "string" ? _ => _.join("") : idem,
       e,
       e);
}
)})
    },
    {
      name: "each",
      inputs: ["iter"],
      value: (function(iter){return(
(collection,functor) => iter(collection,functor,undefined,collection)
)})
    },
    {
      name: "maptype",
      inputs: ["callable","type","idem"],
      value: (function(callable,type,idem){return(
(v,m) => callable(m[type(v)]||m["_"]||idem)(v)
)})
    },
    {
      name: "str",
      value: (function(){return(
_ => "" + _
)})
    },
    {
      name: "until",
      inputs: ["defer"],
      value: (function(defer){return(
(condition, effector, interval=100, delay=0) => {
  const f = () => condition() ? effector(effector) : defer(f, interval)
  defer(f, delay)
  return f;
}
)})
    },
    {
      name: "setattr",
      value: (function(){return(
(node, name, value, append = 0, ns = undefined) => {
  const t = typeof value;
  if (!ns && name.startsWith("on")) {
    const n = name.toLowerCase();
    if (node[n] !== undefined) {
      // We have a callback
      node[n] = value;
    }
    return node;
  }
  if (!ns & (name === "style") && t === "object") {
    // We manage style properties by valle
    if (!append) {
      node.setAttribute("style", "");
    }
    Object.assign(node.style, value);
  } else if (!ns && name === "value" && node.value !== undefined) {
    node.value = value ? value : "";
  } else if (!ns && name.startsWith("on") && node[name] !== undefined) {
    // We have a callback
    node[name] = value;
  } else if (value === undefined || value === null) {
    // We remove the attribute
    ns ? node.removeAttributeNS(ns, name) : node.removeAttribute(name);
  } else {
    // We have a regular value that we stringify
    const v =
      t === "number"
        ? `${value}`
        : t === "string"
        ? value
        : JSON.stringify(value);
    // If we append, we create an inermediate value.
    if (append) {
      const e = ns ? node.getAttributeNS(ns, name) : node.getAttribute(name);
      const w = `${append < 0 && e ? e + " " : ""}${v}${
        append > 0 && e ? " " + e : ""
      }`;
      ns ? node.setAttributeNS(ns, name, w) : node.setAttribute(name, w);
    } else {
      ns ? node.setAttributeNS(ns, name, v) : node.setAttribute(name, v);
    }
  }
  return node;
}
)})
    },
    {
      name: "list",
      inputs: ["maptype","idem"],
      value: (function(maptype,idem){return(
v => maptype(v,{
  null: _ => [],
  undefined: _ => [],
  list: idem,
  _: _ => {
    const n = _.length;
    if (typeof n === "number") {
      const r = [];
      for (var i=0 ; i<n ; i++) {r.push(_[i])}
      return r;
    } else {
      return [v];
    }
  }})
)})
    },
    {
      name: "idem",
      value: (function(){return(
_ => _
)})
    },
    {
      name: "type",
      inputs: ["NodeList","StyleSheetList"],
      value: (function(NodeList,StyleSheetList){return(
_ => _ === null ? "null" : _ instanceof Array || _ instanceof NodeList || _ instanceof StyleSheetList ? "list" : typeof(_)
)})
    },
    {
      name: "empty",
      inputs: ["type"],
      value: (function(type){return(
(value) =>
  value === null || value === undefined
    ? value
    : value instanceof Array
    ? []
    : type(value) === "list"
    ? []
    : type(value) === "object"
    ? {}
    : typeof value === "string"
    ? ""
    : value
)})
    },
    {
      name: "iter",
      inputs: ["idem","isIterator","NodeList","StyleSheetList"],
      value: (function(idem,isIterator,NodeList,StyleSheetList){return(
(
  value,
  iterator = idem,
  processor = idem,
  initial = undefined,
  empty = undefined
) => {
  // TODO: This should be documented
  if (value === undefined || value === null) {
    return processor(initial, value, undefined);
  } else if (typeof value === "string") {
    var i = 0;
    var v = undefined;
    var r = initial;
    const n = value.length;
    while (i < n) {
      v = value.charAt(i);
      const rr = iterator(v, i, r, value);
      if (rr === false) {
        return processor(r, v, i, value);
      } else {
        r = rr === undefined ? r : rr;
      }
      i += 1;
    }
    return i === 0 ? empty : processor(r, v, i, value);
  } else if (typeof value === "object") {
    var v = undefined;
    var r = initial;
    // NOTE: This has to be consistent with type(value) === "list"
    if (isIterator(value)) {
      var i = 0;
      for (let v of value) {
        const rr = iterator(v, i, r, value);
        if (rr === false) {
          return processor(r, v, i, value);
        } else {
          r = rr === undefined ? r : rr;
        }
        i += 1;
      }
      return i === 0 ? empty : processor(r, v, i, value);
    } else if (
      value instanceof Array ||
      value instanceof NodeList ||
      value instanceof StyleSheetList
    ) {
      var i = 0;
      const n = value.length;
      while (i < n) {
        v = value[i];
        const rr = iterator(v, i, r, value);
        if (rr === false) {
          return processor(r, v, i, value);
        } else {
          r = rr === undefined ? r : rr;
        }
        i += 1;
      }
      return i === 0 ? empty : processor(r, v, i, value);
    } else {
      var k = undefined;
      var i = 0;
      for (k in value) {
        v = value[k];
        const rr = iterator(v, k, r, value);
        if (rr === false) {
          return processor(r, v, k, value);
        } else {
          r = rr === undefined ? r : rr;
        }
        i++;
      }
      return i == 0 ? empty : processor(r, v, undefined, value);
    }
  } else {
    return processor(iterator(value, undefined, initial));
  }
}
)})
    },
    {
      name: "callable",
      value: (function(){return(
v => v instanceof Function ? v : () => v
)})
    },
    {
      name: "defer",
      value: (function(){return(
(effector, delay=0, guard=undefined) => delay ? window.setTimeout(guard ? _ => (guard() && effector(effector)) : effector, delay) : effector(effector)
)})
    },
    {
      name: "isIterator",
      value: (function(){return(
(_) =>
  _ &&
  (typeof _.next === "function" || typeof _[Symbol.iterator] === "function")
)})
    }
  ]
};

const notebook = {
  id: "8ed172ec5b1d17d2@230",
  modules: [m0,m1]
};

export default notebook;
