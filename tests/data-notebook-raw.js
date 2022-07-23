// URL: https://observablehq.com/@sebastien/boilerplate
// Title: Boilerplate
// Author: Sébastien Pierre (@sebastien)
// Version: 2228
// Runtime version: 1

const m0 = {
  id: "28e219d819b6b627@2228",
  variables: [
    {
      inputs: ["md"],
      value: (function(md){return(
md`# Boilerplate

This notebook defines a set of useful functions that can help with the creation of interactive documents and examples. It is really a kind of **compact standard library** expressed in a functional style. Its performance is always going to be a bit lower than a purely imperative equivalent, but it offers a more expresssive, declarative API.

The functions available are grouped according to the following sections:

- *Primitive functions* to work with primitive data types: <code>bool,str,list</code> and <code>type,maptype</code>
- *Functional tools* that help with functional programm: <code>idem,swallow,effect</code> and <code>callable,def</code>
- *Collection functions* that work with arrays and maps: <code>values,keys,head,tail,nth</code> to access, <code>iter,each,map,filter,reducer</code> for transformation,  <code>first</code> for query and <code>merge,itemize</code> as helpers.
- *Math functions*, <code>min,max,minmax,sign,order</code> to get numeric information, <code>lerp,prel,scale,clamp,step,smoothstep</code> for interpolation and transformtion,  <code>range,closest,nicer</code> to work with ranges.

There is another set of functions related to interface, rendering and interactivity:
- *DOM functions* to create styles and elements: <code>stylesheet,css,style</code> to define stylehseets, <code>html,html.{create,append,set,clear}</code> to create and update DOM nodes and <code>toggle,show,hide</code> to change visibility.
- *Event handling* with <code>on,off,keywap</code> to interface with DOM events, and <code>bind,unbind,trigger</code> for pure ad-hoc event pub/sub.

The functions are implement in a compact and hopefully readable way, in doubt about the behaviour, look a the source and play with the functions interactively!
`
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`# Primitive Functions

- <code>bool(v)</code>
- <code>str(v)</code> returns *v* as a string
- <code>list(v)</code>
- <code>empty(v)</code> returns an <code>[]</code> if *v* is a list, <code>{}</code> if it is an object, or *v* otherwise.
- <code>type(v)</code>
- <code>maptype(v,d)</code> resolves the mapping of *type(v)* in *d*, defaulting to <code>_</code> and then *idem*

`
)})
    },
    {
      name: "bool",
      value: (function(){return(
(_) =>
  _ === "true"
    ? true
    : _ === "false"
    ? false
    : _ instanceof Array
    ? _.length > 0
    : _ instanceof Object
    ? Object.keys(_).length > 0
    : false
)})
    },
    {
      name: "str",
      value: (function(){return(
_ => "" + _
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
      name: "cmp",
      value: (function(){return(
(()=>{const cmp = (a, b) => {
    //if (a === undefined) {
    //    return b === undefined ? 0 : -cmp(b, a);
    //}
    const ta = typeof a;
    const tb = typeof b;
    if (ta === tb) {
        switch (ta) {
            case "string":
                return a.localeCompare(b);
            case "object":
                if (a === b) {
                    return 0;
                } else if (a instanceof Array) {
                    const la = a.length;
                    const lb = b.length;
                    if (la < lb) {
                        return -1;
                    } else if (la > b) {
                        return 1;
                    } else {
                        var i = 0;
                        while (i < la) {
                            const v = cmp(a[i], b[i]);
                            if (v !== 0) {
                                return v;
                            }
                          i += 1;
                        }
                        return 0;
                    }
                } else {
                    return -1;
                }
            default:
                return a === b ? 0 : a > b ? 1 : -1;
        }
    } else {
        return a === b ? 0 : a > b ? 1 : -1;
    }
}; return cmp})()
)})
    },
    {
      name: "eq",
      inputs: ["type"],
      value: (function(type){return(
(()=>{const eq = (a, b) => {

    if (a === b) {return true}
    const ta = type(a);
    const tb = type(b);
  
    if (ta === tb) {
        switch (ta) {
            case "string":
              return a == b;
            case "list":
              const la = a.length;
              const lb = b.length;
              if (la !== lb) {
                return false;
              } else {
                var i = 0;
                while (i < la) {
                  if (!eq(a[i], b[i])) {
                    return false;
                  }
                  i += 1;
                }
                return true;
              }
            case "object":
              // TODO: We might want to do that with keys
              return a === b;
            default:
                return a == b;
        }
    } else {
        return a == b;
    }
}; return eq})()
)})
    },
    {
      name: "is",
      value: (function(){return(
(v,...args) => {
  var i = 0;
  while (i < args.length ) {
    if (v === args[i]) {return true}
    else {i++}
  }
  return false
}
)})
    },
    {
      name: "hasChanged",
      inputs: ["eq"],
      value: (function(eq){return(
(a,b) => !eq(a,b)
)})
    },
    {
      name: "isDef",
      value: (function(){return(
_ => _ !== undefined
)})
    },
    {
      name: "isValue",
      value: (function(){return(
_ => _ !== undefined && _ != null
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`The *list* function will force the conversion of a value to a list. If the value has a <code>length</code> attribute as as a number, then its component will be extracted by index even if the type of the value is not a list. This is useful to force any object that is not identified as a list to behave like one, provided it implements a <code>length</code> property.`
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
      name: "iterable",
      inputs: ["list"],
      value: (function(list){return(
_ => _ instanceof Object ? _ : list(_)
)})
    },
    {
      name: "asMappable",
      value: (function(){return(
functor => _ => _ instanceof Array ? _.map(_ => functor(_)) : functor(_)
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
      name: "maptype",
      inputs: ["callable","type","idem"],
      value: (function(callable,type,idem){return(
(v,m) => callable(m[type(v)]||m["_"]||idem)(v)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`TODO: Optimise`
)})
    },
    {
      name: "copy",
      inputs: ["Node","maptype","idem","map"],
      value: (function(Node,maptype,idem,map){return(
(() => {
  const copy = (v, depth = 1) =>
    depth == 0
      ? v
      : v instanceof Node
      ? v.cloneNode(true)
      : maptype(v, {
          string: idem,
          number: idem,
          null: (_) => null,
          undefined: (_) => undefined,
          _: (_) => map(_, (_) => copy(_, depth - 1))
        });
  return copy;
})()
)})
    },
    {
      name: "isMap",
      value: (function(){return(
_ => _ !== null && (_ instanceof Map || _ instanceof Object && !(_ instanceof Array))
)})
    },
    {
      name: "isList",
      value: (function(){return(
_ => _ instanceof Array
)})
    },
    {
      name: "isIterator",
      value: (function(){return(
(_) =>
  _ &&
  (typeof _.next === "function" || typeof _[Symbol.iterator] === "function")
)})
    },
    {
      name: "isCollection",
      inputs: ["_"],
      value: (function(_){return(
(value) => _ !== null && typeof value === "object"
)})
    },
    {
      name: "isIterable",
      value: (function(){return(
(_) =>
  // FIXME: Not sure about that one, see isCollection
  _ !== null && _ instanceof Object
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`### Symbols`
)})
    },
    {
      name: "Nothing",
      value: (function(){return(
new String("Nothing")
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Functional Tools

We define a set of general purpose functions that help write notebooks in a more functional style.

- <code>idem(v)</code> returns *v*
- <code>swallow(a,b)</code> evaluates *a* and returns *b*
- <code>effect(v,f)</code> like *swallow(f(v),v)*
- <code>callable(f)</code> ensures that *f* is a function, if not wraps it in a function that returns *f*
- <code>def(v,...)</code> returns the first defined argument
`
)})
    },
    {
      name: "idem",
      value: (function(){return(
_ => _
)})
    },
    {
      name: "swallow",
      value: (function(){return(
(a,b) => b
)})
    },
    {
      name: "nop",
      value: (function(){return(
() => {}
)})
    },
    {
      name: "effect",
      inputs: ["swallow"],
      value: (function(swallow){return(
(v,f) => swallow(f(v), v)
)})
    },
    {
      name: "pipe",
      value: (function(){return(
(v,...f) => {var r=v;for(var i=0;i<f.length;i++){r=f[i](r)};return r}
)})
    },
    {
      name: "compose",
      value: (function(){return(
(...args) => {
  const n = args.length;
  if (n == 2) {return _ => args[1](args[0](_))}
  else if (n == 3) {return _ => args[2](args[1](args[0](_)))}
  throw new window.Exception("Not supported");
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
      name: "def",
      inputs: ["first"],
      value: (function(first){return(
(...values) => first(values, _ => _ !== undefined)
)})
    },
    {
      name: "memoize",
      value: (function(){return(
(producer, key=true, store=undefined) => {
  var state   = undefined
  var trigger = undefined
  return ()=> {
    const t = store ? store(key,key) : trigger
    if (t !== key) {
      trigger = store ? store(key,t) : trigger
      key=trigger;state=producer();}
    return state;
  }
}
)})
    },
    {
      name: "freeze",
      value: (function(){return(
value => value instanceof Object && Object.freeze(value) ? value : value
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`# State`
)})
    },
    {
      name: "state",
      value: (function(){return(
( ()=>{
  const state = {};
  return (name,value=undefined) => {
    if (value === undefined) {
      return state[name];
    } else {
      state[name] = value;
      return value;
    }
  }
})()
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`# Collections Functions

This is a set of functions that work with both lists and objects and make it easy to extract information.

Access functions:

- *values(collection)*
- *keys(collection)*
- *head(collection)*
- *nth(collection,index)*

Query functions:

- *first(collection,predicate)*

Transformation functions:

- *iter(collection,functor,processor,initial)*
- *map(collection,processor)*
- *filter(collection,predicate,processor)*


`
)})
    },
    {
      name: "len",
      inputs: ["maptype"],
      value: (function(maptype){return(
v => maptype(v,{
  list: _ => _.length,
  object: _ => typeof _.length === "number" ? _.length : Object.keys(v).length,
  string: _ => _.length,
  _:1,
  null: _ => 0,
  undefined: _ => 0})
)})
    },
    {
      name: "values",
      inputs: ["maptype","idem"],
      value: (function(maptype,idem){return(
v => maptype(v,{
  list: idem,
  object: _ => Object.values(v),
  _:[v],
  null: _ => [],
  undefined: _ => []})
)})
    },
    {
      name: "keys",
      inputs: ["maptype"],
      value: (function(maptype){return(
v => maptype(v,{
  list: _ => _.map( (_,i) => i ),
  object: _ => Object.keys(v),
  _:[v],
  null: _ => [],
  undefined: _ => []})
)})
    },
    {
      name: "items",
      inputs: ["type"],
      value: (function(type){return(
(collection, asList=true) => {
  let isList = false;
  // TODO: Should use iter
  switch (type(collection)) {
    case "list":
      isList = true;
    case "object":
      const res = [];
      let i=0;
      if (asList) {
        for (let k in collection) {
            res[i++] = [isList ? i : k, collection[k]];
        }
      } else {
         for (let k in collection) {
            res[i++] = {key:k, value:collection[k]};
        }
      }
      return res;
    default:
      return []
  }
}
)})
    },
    {
      name: "keyvalues",
      inputs: ["items"],
      value: (function(items){return(
_ => items(_, false)
)})
    },
    {
      inputs: ["first"],
      value: (function(first){return(
first([1, 2, 3])
)})
    },
    {
      inputs: ["first"],
      value: (function(first){return(
first({a:1, b:2, c:3})
)})
    },
    {
      name: "first",
      inputs: ["idem","iter","nth"],
      value: (function(idem,iter,nth){return(
(value, predicate = null, processor = idem) =>
  predicate
    ? iter(
        value,
        (v, i) => (predicate ? predicate(v, i, value) !== true : true),
        (r, v, i) => processor(value[i], i)
      )
    : processor(nth(value, 0), 0)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`*Note*: at some point \`index()\` returned \`undefined\` when the collection was not \`null\` or \`undefined\`, this is now changed to \`-1\` all the time.`
)})
    },
    {
      name: "index",
      value: (function(){return(
(collection, value) => {
  if (collection instanceof Array) {
    return collection.indexOf(value);
  } else if (collection instanceof Object) {
    for (let k in collection) {
      if (collection[k] === value) {
        return k;
      }
    }
  }
  return -1;
}
)})
    },
    {
      name: "indexLike",
      inputs: ["iter"],
      value: (function(iter){return(
(collection, predicate) =>
  iter(
    collection,
    (_) => !predicate(_),
    (r, v, i) => i
  )
)})
    },
    {
      name: "head",
      inputs: ["values"],
      value: (function(values){return(
(value, count) => {
  const v = values(value);
  return count === undefined || count === 0
    ? v[0]
    : v.slice(0, count < 0 ? v.length + count : count);
}
)})
    },
    {
      name: "nth",
      inputs: ["values"],
      value: (function(values){return(
(value, index = 0) => {
  const v = values(value);
  return v[index < 0 ? v.length + index : index];
}
)})
    },
    {
      name: "access",
      value: (function(){return(
(collection, path) => typeof collection === "object" 
  ? (typeof path === "string" ? collection[path] : path.reduce((r,v) => typeof r === "object" ? r[v] : undefined, collection))
  : undefined
)})
    },
    {
      name: "last",
      inputs: ["nth"],
      value: (function(nth){return(
value => nth(value, -1)
)})
    },
    {
      name: "unique",
      inputs: ["filter"],
      value: (function(filter){return(
(collection) => {
  const l = [];
  return filter(collection, _ =>  l.indexOf(_) !== -1 ? false : l.push(_)||true)
}
)})
    },
    {
      name: "pick",
      inputs: ["values","nth","len"],
      value: (function(values,nth,len){return(
(items) => {
  const l = values(items)
  return nth(values(l),Math.round(Math.random() * (len(l)-1)))
}
)})
    },
    {
      name: "isIn",
      inputs: ["index"],
      value: (function(index){return(
(collection, value) => index(collection, value) !== -1
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`
The *iter* function is a versatile function that can be used to implement map/reduce/filter functions that work across all the types of objects 
`
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Boolean operations`
)})
    },
    {
      name: "difference",
      inputs: ["filter","index"],
      value: (function(filter,index){return(
(a,b) => filter(a, _ => index(b,_) == -1)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`### Updaters

Update functions will generate a new collection with the applied operation without modifying the collection.
`
)})
    },
    {
      name: "set",
      inputs: ["copy"],
      value: (function(copy){return(
(scope,key,value) => {
  const res = copy(scope);
  if (scope instanceof Array && key instanceof Number) {
    while(res.length < key) {res.push(undefined)}
    res[key] = value;
    return res;
  } else {
    res[key]=value;
    return res
  }
}
)})
    },
    {
      name: "has",
      inputs: ["type"],
      value: (function(type){return(
(collection,item) => {
  switch (type(collection)) {
    case "list": 
      return (collection.indexOf(item) !== -1) 
    case "object":
      for (let k in collection) {if (collection[k] === item) {return true}}
      return false;
    default:
      return false;
  }
}
)})
    },
    {
      name: "ensure",
      inputs: ["type"],
      value: (function(type){return(
(collection,item) => {
  switch (type(collection)) {
    case "list":
      if (collection.indexOf(item) === -1) {
        const res = collection.slice()
        res.push(item);
        return res;
      } else {
        return collection;
      }
    case "object":
      let i = 0;
      for (let k in collection) {
        if (collection[k] === item) {return collection} 
        i++;
      }
      while(collection[i]){i++}
      const r = {};
      Object.assign(r,collection);
      r[i]=item;
      return r;
    default:
      return collection;
  }
}
)})
    },
    {
      name: "prepend",
      inputs: ["type","list"],
      value: (function(type,list){return(
(()=>{
  const prepend = (collection, item) => {
      switch (type(collection)) {
      case "list":
        const res = collection.slice();
        res.splice(0,0,item);
        return res;
      case "object":
        const r = {};
        let i = 0;
        while (collection[i] !== undefined) {i++}
        r[i] = item;
        Object.assign(r, collection);
        return r;
      default:
        return prepend(list(collection), item);
    }
  };
  return prepend;
})()
)})
    },
    {
      name: "append",
      inputs: ["type","list"],
      value: (function(type,list){return(
(() => {
  const append = (collection, item, isMutable = false) => {
    switch (type(collection)) {
      case "list":
        const res = isMutable ? collection : collection.slice();
        res.push(item);
        return res;
      case "object":
        const r = isMutable ? collection : Object.assign({}, collection);
        let i = Object.entries(r).length;
        while (r[i] !== undefined) {
          i++;
        }
        r[i] = item;
        return r;
      default:
        return append(list(collection), item, isMutable);
    }
  };
  return append;
})()
)})
    },
    {
      name: "remove",
      inputs: ["type"],
      value: (function(type){return(
(collection,item) => {
  switch (type(collection)) {
    case "list":
      if (collection.indexOf(item) === -1) {
        return collection;
      } else {
        return collection.filter( _ => _ !== item);
      }
    case "object":
      let found = false;
      for (let k in collection) {
        if (collection[k] === item) {found=true;break} 
      }
      if (found) {
        const r = {};
        for (let k in collection) {
          if (collection[k] !== item) {r[k]=collection[k]}
        }
        return r
      } else {
        return collection
      }
    default:
      return collection;
  }
}
)})
    },
    {
      name: "toggle",
      inputs: ["has","remove","append"],
      value: (function(has,remove,append){return(
(collection,item) => has(collection,item) ? remove(collection,item) : append(collection,item)
)})
    },
    {
      name: "insertAt",
      inputs: ["type","copy","list"],
      value: (function(type,copy,list){return(
(collection, index, item) => {
  const res = type(collection) === "list" ? copy(collection) : list(collection);
  const i = index < 0 ? res.length + index : index
  res.splice(i, 0, item);
  return res;
}
)})
    },
    {
      name: "removeAt",
      inputs: ["filter"],
      value: (function(filter){return(
(collection, index) => filter(collection, (v,i) => i !== index)
)})
    },
    {
      name: "slice",
      inputs: ["len","filter","within"],
      value: (function(len,filter,within){return(
(collection, min, max=undefined) => {
  const mn = max === undefined ? 0 : min;
  const mx = max === undefined ? min : max;
  const n = len(collection)
  const imn = mn < 0 ? Math.min(n-1,n+mn) : mn;
  const imx = mx < 0 ? Math.min(n,n+mx) : mx;
  return filter(collection, (v,i)=>within(i, imn, imx - 1))
}
)})
    },
    {
      name: "concat",
      inputs: ["list"],
      value: (function(list){return(
(a,b) => list(a).concat(list(b))
)})
    },
    {
      name: "clampsize",
      inputs: ["idem","len","resize"],
      value: (function(idem,len,resize){return(
(collection, min, max, creator=idem) => {
  const n = len(collection)
  if      (n < min) {return resize(collection,min,creator)}
  else if (n > max) {return resize(collection,max,creator)}
  else              {return collection}
}
)})
    },
    {
      name: "resize",
      inputs: ["idem","len","concat","slice"],
      value: (function(idem,len,concat,slice){return(
(values, size, creator = idem) => {
    let n = len(values);
    if (n < size) {
        const suffix = [];
        while (n < size) {
            suffix.push((creator||idem)(n++));
        }
        return concat(values, suffix)
    }
    else if (n > size) {
        return slice(values, 0, size);
    }
    else {
        return values;
    }
}
)})
    },
    {
      name: "grow",
      inputs: ["isDef","resize","max","len"],
      value: (function(isDef,resize,max,len){return(
(array,size,creator) => isDef(size) ? resize(array, max(size,len(array)), creator) : array
)})
    },
    {
      name: "reverse",
      inputs: ["type","array"],
      value: (function(type,array){return(
(collection) => {
  const t = type(collection);
  switch (t) {
    case "list":
      const n = collection.length;
      return array(n, i => collection[n - i - 1]); 
    case "object":
      const l = Object.keys(collection);
      const r = {};
      for (let i=l.length - 1 ; i>=0 ; i--) {
        const k = l[i];
        r[k] = collection[k];
      }
      return r;
    default:
      return collection;
   }
}
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`### Iter, Map, Filter, Reduce

These collection function all work across lists and objects and are based on the primitive *iter* function. They differ a bit from the <code>Array.{forEach,filter,map}</code> primitives as they will return a result of the same type as the collection and that the functors, predicate typically take *(value,key,collection)* instead of just *(value,key)*.
`
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
      inputs: ["md"],
      value: (function(md){return(
md`The *map(collection,functor)* function works with boths lists and objects. The functor takes *(value,key,collection)& as arguments. Under the hood, the *map* function uses the *iter* function.`
)})
    },
    {
      name: "array",
      value: (function(){return(
(count,creator=null) => {
  const res = new Array(count);
  while(count) {count--;res[count] = creator ? creator(count) : count}
  return res;
}
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
      name: "mapkeys",
      inputs: ["reduce","empty"],
      value: (function(reduce,empty){return(
(collection, functor) =>
  reduce(
    collection,
    (r, v, k) => {
      r[functor(k, v)] = v;
    },
    empty(collection)
  )
)})
    },
    {
      name: "maplist",
      inputs: ["reduce"],
      value: (function(reduce){return(
(collection,functor) =>
  reduce(collection, (r,v,k,l)=>{r.push(functor(v,k,l));}, [])
)})
    },
    {
      name: "reduce",
      inputs: ["iter","idem","empty"],
      value: (function(iter,idem,empty){return(
(collection,processor,initial=undefined) =>
  iter(collection,
      (v,k,r) => {const w=processor(r,v,k,collection);return w === undefined ? r : w},
      idem,
      initial === undefined ? empty(collection) : initial,
      initial)
)})
    },
    {
      name: "filter",
      inputs: ["bool","idem","iter","type","empty"],
      value: (function(bool,idem,iter,type,empty){return(
(collection, predicate=bool, processor=idem) =>
  iter(collection, 
       type(collection) === "list" 
       ? (v,i,r) => {predicate(v,i,collection) !== false && r.push(processor(v,i));return r}
       : (v,k,r) => {if (predicate(v,k,collection) !== false) {r[k]=processor(v,k)};return r},
       idem,
       empty(collection),
       collection)
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
      name: "merge",
      value: (function(){return(
(value, other, replace = false) => {
  if (value === null || value === undefined) {
    return other;
  } else if (other === null || value === other) {
    return value;
  } else {
    for (let k in other) {
      const v = value[k];
      const w = other[k];
      if (v === undefined) {
        value[k] = w;
      } else if (replace === true) {
        value[k] = w;
      } else if (replace instanceof Function) {
        value[k] = replace(value[k], w);
      }
    }
    return value;
  }
}
)})
    },
    {
      name: "rmerge",
      inputs: ["reduce"],
      value: (function(reduce){return(
(() => {
  const rmerge = (value, other, depth = -1) => {
    if (depth === 0) {
      return value;
    } else if (value === null || value === undefined) {
      return other;
    } else if (other === null || value === other) {
      return value;
    } else if (other instanceof Object && value instanceof Object) {
      return reduce(
        other,
        (r, v, k) => {
          r[k] = rmerge(r[k], v, depth > 0 ? depth - 1 : depth);
        },
        value
      );
    } else {
      return other;
    }
  };
  return rmerge;
})()
)})
    },
    {
      name: "groupBy",
      inputs: ["reduce"],
      value: (function(reduce){return(
(collection, extractor, processor=undefined) => 
reduce(collection,(r,v,k)=>{
  const g = extractor(v,k,collection);
  (r[g] = r[g] || []).push(processor ? processor(v) : v);
  return r;
}, [])
)})
    },
    {
      name: "partition",
      inputs: ["reduce"],
      value: (function(reduce){return(
(collection,predicate) => (collection instanceof Array
  ? reduce(collection, (r,v,i) => {r[predicate(v,i) ? 0 : 1].push(v)}, [[],[]])
  : reduce(collection, (r,v,k) => {r[predicate(v,k) ? 0 : 1][k] = v} , [{},{}])) || [[],[]]
)})
    },
    {
      name: "sorted",
      inputs: ["cmp","idem","list"],
      value: (function(cmp,idem,list){return(
(collection, key=undefined, ordering=1, comparator=cmp) => {
    const extractor =
        typeof key === "function"
            ? key
            : key
            ? _ => (_ ? _[key] : undefined)
            : idem;
    const res =
        collection instanceof Array ? [].concat(collection) : list(collection);
    res.sort((a, b) => ordering * (key ? comparator(extractor(a), extractor(b)) : comparator(a, b)));
    
    return res;
}
)})
    },
    {
      name: "flatten",
      inputs: ["isCollection","list","reduce","concat"],
      value: (function(isCollection,list,reduce,concat){return(
(() => {
  const flatten = (value, depth = -1) => {
    if (depth === 0 || !isCollection(value)) {
      return list(value);
    } else {
      return reduce(value, (r, v) => concat(r, flatten(v, depth - 1)), []);
    }
  };
  return flatten;
})()
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`### Collection utilities`
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`\`enumerate("A", "B", ..)\` will return \`{A:"A",B:"B"B,...}\` as a frozen object.`
)})
    },
    {
      name: "enumerate",
      inputs: ["freeze","reduce"],
      value: (function(freeze,reduce){return(
(...values) =>
  freeze(
    reduce(
      values,
      (r, v) => {
        r[v] = v;
        return r;
      },
      {}
    )
  )
)})
    },
    {
      name: "itemize",
      inputs: ["isMap","reduce","list","merge","str"],
      value: (function(isMap,reduce,list,merge,str){return(
l => isMap(l) ?
  reduce(l, (r,v,k)=> {
    r.push({label:k, key:k, index:r.length, value:v})
  }, [])
:
  list(l).map( (_,i) => merge({index:i,key:i}, _ && _.value !== undefined ? _ : {value:_, label:str(_)}))
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`We define the *combinations(values,k)* function that returns the list of combinations of *k* elements out of values (order not important).`
)})
    },
    {
      name: "combinations",
      inputs: ["len","range"],
      value: (function(len,range){return(
(values,k=2) => {
  // Straight port of: https://docs.python.org/3.8/library/itertools.html#itertools.combinations
  const res = [];
  const n = len(values);
  // We cannot have k > n
  if (k > n) {return res};
  // We're going to mutate the indicies, but right now it's going to
  // be 0..k
  const indices = range(k);
  // And the first value we add is the first k values of our set
  res.push(indices.map(_ => values[_]));
  // Now that's the loop
  while (true) {
    // We iterate in on 0..k in reverse
    let found = undefined;
    for (let i = k-1 ; i >=0 ; i--) {
      // NOTE: Not sure what happens here
      if (indices[i] !== i + n - k) {
        found = i;
        break}}
    // If we did not find that indice, we're done!
    if (found===undefined) {return res;}
    indices[found] += 1
    // TODO: Not sure what happens there either
    for (let j=found+1 ; j<k ; j++) {
       indices[j] = indices[j-1] + 1
    }
    res.push(indices.map( _ => values[_] ));}
  return res;
}
)})
    },
    {
      name: "stripe",
      inputs: ["len","array"],
      value: (function(len,array){return(
(values) => {
  const n = len(values);
  const m = Math.floor(n/2);
  return array(n, i =>
    values[i < m 
    ? Math.min(n-1,i * 2)
    : Math.min(n-1,1 + (i-m)*2)]
  )
}
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`# Math Functions`
)})
    },
    {
      name: "sign",
      value: (function(){return(
(value) => 
   value < 0 ? -1 : 1
)})
    },
    {
      name: "order",
      value: (function(){return(
(value, base = 10) =>
   Math.log(Math.abs(value)) / Math.log(base)
)})
    },
    {
      name: "lerp",
      value: (function(){return(
(a, b, k) => {
  k = k === undefined ? 0.5 : k
  return a + (b - a) * k
}
)})
    },
    {
      name: "prel",
      value: (function(){return(
(v, a, b) =>
   (v - a) / (b - a)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Step functions

Use [Desmos](https://www.desmos.com/calculator) to chart, and more details [here](https://en.wikipedia.org/wiki/Smoothstep).`
)})
    },
    {
      name: "sinestep",
      value: (function(){return(
x => (Math.cos(Math.PI+Math.PI*x) + 1) / 2
)})
    },
    {
      name: "smoothstep",
      value: (function(){return(
x => x * x * x * (x * (x * 6 - 15) + 10)
)})
    },
    {
      name: "smootherstep",
      value: (function(){return(
x => x*x*x*(x*(x*6-15)+10)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Numerical bounds`
)})
    },
    {
      name: "clamp",
      value: (function(){return(
(v, a, b) => Math.max(a, Math.min(b, v))
)})
    },
    {
      name: "round",
      value: (function(){return(
(number, factor = 1, bound = 1) => {
  const base = number / factor
  const roundedBase =
        bound < 0
          ? Math.floor(base)
          : bound > 0
            ? Math.ceil(base)
            : Math.round(base)
  return roundedBase * factor
}
)})
    },
    {
      name: "min",
      value: (function(){return(
(()=>{
  const min = (...args) =>
  args.length === 1 ? (args[0] instanceof Array ?args[0].reduce((r,v)=>r === undefined ? v : min(r,v)) : args[0]) :
  args.length === 2 ? Math.min(min(args[0]), min(args[1]))
  : args.reduce((r,v)=>r === undefined ? v : min(r,v))
return min})()
)})
    },
    {
      name: "max",
      value: (function(){return(
(()=>{
  const max = (...args) =>
  args.length === 1 ? (args[0] instanceof Array ?args[0].reduce((r,v)=>r === undefined ? v : max(r,v)) : args[0]) :
  args.length === 2 ? Math.max(max(args[0]), max(args[1]))
  : args.reduce((r,v)=>r === undefined ? v : max(r,v))
return max})()
)})
    },
    {
      name: "minmax",
      inputs: ["list","min","max"],
      value: (function(list,min,max){return(
(()=>{
  const minmax = (...args) => {
    if (args.length === 1) {
      return list(args[0]).reduce((r, v, i) => {
        if (i === 0) {
          r[0] = r[1] = v;
        } else {
          r[0] = min(r[0], v);
          r[1] = max(r[1], v);
        }
        return r;
      }, [undefined, undefined])
    } else {
      return minmax(args);
    }
  }
  return minmax;
})()
)})
    },
    {
      name: "maxmin",
      inputs: ["minmax"],
      value: (function(minmax){return(
(...args) => {
  const [a,b] = minmax(...args);
  return [b,a]
}
)})
    },
    {
      name: "wrap",
      value: (function(){return(
(v,base=10) => {
  const b = Math.abs(base)
  return b === 0 || v===0 ? 0 :
    v > 0 ? v % b : (b + (v % b)) % b;}
)})
    },
    {
      name: "range",
      value: (function(){return(
(start, end, step = 1, closed = false) => {
  if (end === undefined) {end=start;start=0}
  const n = Math.ceil(Math.max(0, (end - start) / step)) + (closed ? 1 : 0)
  const r = new Array(n)
  var v = start
  for (let i = 0; i < n; i++) {
    r[i] = v
    v += step
  }
  return r
}
)})
    },
    {
      name: "closest",
      inputs: ["dist","reduce"],
      value: (function(dist,reduce){return(
(values, value, distance=dist) => 
  reduce(values, (r,v,i)=>{
    const d = distance(v,value);
    if (i === 0 || r.dist > d) {
      r.dist = d;
      r.value = v;
    }
    return r
  }, {dist:undefined, value:undefined}).value
)})
    },
    {
      name: "closestInOrder",
      value: (function(){return(
(values, value, affinity = 0) => {
  var i = 0
  const n = values.length
  var last = 0
  while (i < n) {
    const current = values[i]
    if (value === current) {
      return value
    } else if (value < current) {
      if (i === 0) {
        return current
      } else {
        if (affinity === 0) {
          return value - last < current - value ? last : current
        } else if (affinity < 0) {
          return last
        } else {
          return current
        }
      }
    }
    last = current
    i += 1
  }
  return last
}
)})
    },
    {
      name: "nicer",
      inputs: ["sign","order","closestInOrder"],
      value: (function(sign,order,closestInOrder){return(
(value, affinity = 0, values = [1, 5, 10, 20, 25, 50, 100]) => {
  const v = Math.abs(value)
  const s = sign(value)
  const k = Math.pow(10, Math.floor(order(v)) -1)
  return s * closestInOrder(values, v/k, affinity*s) * k
}
)})
    },
    {
      name: "within",
      value: (function(){return(
(v,a,b) => a <= v && v <= b
)})
    },
    {
      name: "subdivide",
      inputs: ["range"],
      value: (function(range){return(
(start=0,end=1,steps=100,closed=true) => 
  // TODO: Support nice start and end?
  steps <= 0 
  ? [] 
  : start===end 
  ? (closed ? [start] : [])
  : range(start,end,(end-start)/(steps - (closed ? 1 : 0)),closed)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`
### Numerical operations
`
)})
    },
    {
      name: "add",
      inputs: ["reduce"],
      value: (function(reduce){return(
(a,b) => a instanceof Array ? reduce(a,(r,v)=>r+v,0) : a + b
)})
    },
    {
      name: "sub",
      value: (function(){return(
(a,b) => a instanceof Array ? a[0] - a[1] : a - b
)})
    },
    {
      name: "mul",
      inputs: ["reduce"],
      value: (function(reduce){return(
(a,b) => a instanceof Array ? reduce(a,(r,v)=>r*v,1) : a * b
)})
    },
    {
      name: "sq",
      value: (function(){return(
v => v * v
)})
    },
    {
      name: "sqrt",
      value: (function(){return(
v => Math.sqrt(v)
)})
    },
    {
      name: "sqdist",
      inputs: ["sq","sub"],
      value: (function(sq,sub){return(
(a,b) => sq(sub(a,b))
)})
    },
    {
      name: "dist",
      value: (function(){return(
(a,b) => Math.abs(b - a)
)})
    },
    {
      name: "reldist",
      value: (function(){return(
(a,b) => (b-a)/b
)})
    },
    {
      name: "circdist",
      value: (function(){return(
(a,b) => {
  const d =  Math.abs(b - a) % 1.0;
  return d > 0.5 ? 1 - d : d;
}
)})
    },
    {
      name: "factorial",
      value: (function(){return(
n => {
  var res = n;
  while (n > 0) {res *= n--}
  return res;
}
)})
    },
    {
      name: "cnk",
      inputs: ["factorial"],
      value: (function(factorial){return(
(n,k) => factorial(n)/(factorial(k)*factorial(n-k))
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`### Numerical series operations`
)})
    },
    {
      name: "sum",
      inputs: ["reduce","add"],
      value: (function(reduce,add){return(
collection => reduce(collection, add, 0)
)})
    },
    {
      name: "extent",
      inputs: ["sub","minmax"],
      value: (function(sub,minmax){return(
series => Math.abs(sub(minmax(series)))
)})
    },
    {
      name: "midpoint",
      inputs: ["lerp","minmax"],
      value: (function(lerp,minmax){return(
series => lerp(...minmax(series), 0.5)
)})
    },
    {
      name: "gradients",
      inputs: ["reduce","list"],
      value: (function(reduce,list){return(
series =>
  reduce(list(series), (r,v,i,l) => {i > 0 && r.push(v - l[i -1])})
)})
    },
    {
      name: "mean",
      inputs: ["sum","len"],
      value: (function(sum,len){return(
series =>
  sum(series)/len(series)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`*rmsd(series,target)* computes the [root mean square deviation](https://en.wikipedia.org/wiki/Root-mean-square_deviation) of a series relative to the target.`
)})
    },
    {
      name: "rmsd",
      inputs: ["reduce","sqdist","len"],
      value: (function(reduce,sqdist,len){return(
(series, target=1) =>
 Math.sqrt(reduce(series, (r,v) => r + sqdist(v, target), 0) / len(series))
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Text Functions`
)})
    },
    {
      name: "reducematches",
      value: (function(){return(
(text, regexp, reducer, initial = []) => {
  let res = initial;
  let i = 0;
  let o = 0;
  let r = undefined;
  for (const match of text.matchAll(regexp)) {
    if (o != match.index) {
      r = reducer(res, text.substring(o, match.index), i++);
    }
    res = r === undefined ? res : r;
    r = reducer(res, match, i++);
    o = match.index + match[0].length;
    res = r === undefined ? res : r;
  }
  if (o != text.length) {
    r = reducer(res, text.substring(o), i++);
  }
  res = r === undefined ? res : r;
  return res;
}
)})
    },
    {
      name: "toKebabCase",
      inputs: ["reduce"],
      value: (function(reduce){return(
(words) => reduce(words, (r,v) => {r.push(v.toLowerCase())}, []).join("-")
)})
    },
    {
      name: "fromKebabCase",
      value: (function(){return(
(text) => text.split("-").map((_) => _.strip())
)})
    },
    {
      inputs: ["fromPascalCase"],
      value: (function(fromPascalCase){return(
fromPascalCase("CommandOutput")
)})
    },
    {
      name: "fromPascalCase",
      inputs: ["reducematches"],
      value: (function(reducematches){return(
(text) =>
  reducematches(text, /[A-Z][a-z]+/g, (r, v) => {
    r.push(typeof v === "string" ? v : v[0]);
  })
)})
    },
    {
      inputs: ["capitalize"],
      value: (function(capitalize){return(
capitalize("hello")
)})
    },
    {
      name: "capitalize",
      value: (function(){return(
(text) => `${text.substr(0, 1).toUpperCase()}${text.substr(1)}`
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`
## Data Processing functions

A set of functions for working with data, and in particular numerical data. Note: this functions should probably be moved to another notebook as they're quite specific to numerical series.
`
)})
    },
    {
      name: "describe",
      inputs: ["reduce"],
      value: (function(reduce){return(
(series) => {
  const res = reduce(
    series,
    (r, v, k) => {
      r.min = Math.min(r.min === undefined ? v : r.min, v);
      r.max = Math.max(r.max === undefined ? v : r.min, v);
      r.total += v;
      r.count += 1;

      return r;
    },
    {
      min: undefined,
      max: undefined,
      total: 0,
      count: 0,
      mean: 0,
      variance: 0,
      deviation: 0,
      values: series
    }
  );
  res.mean = res.total / res.count;
  // FROM: https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
  // We do a two pass-algorithm as it's safer
  let m = res.mean;
  res.variance =
    reduce(
      series,
      (r, v, k) => {
        const dm = v - m;
        return r + dm * dm;
      },
      0
    ) / res.count;
  res.deviation = Math.sqrt(res.variance);
  return res;
}
)})
    },
    {
      name: "delta",
      inputs: ["sub"],
      value: (function(sub){return(
(series,distance=sub) => series.reduce((r,v,i)=>{
  if (i > 0) {r.push(distance(v, series[i - 1]))}
  return r;
}, [])
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`
### Text processing functions`
)})
    },
    {
      name: "safekey",
      value: (function(){return(
(()=>{
  const RE_OFFKEY = new RegExp ("([^A-Za-z0-9 \t\n])", "g");
  const RE_SPACES = new RegExp ("[ \t\n]+", "g")
  return (_,sep="_") =>
    ("" + _).trim().replace(RE_OFFKEY, "_").replace(RE_SPACES, sep)
})()
)})
    },
    {
      name: "uid",
      value: (function(){return(
() =>
  // FROM: https://stackoverflow.com/questions/6248666/how-to-generate-short-uid-like-ax4j9z-in-js
  // I generate the UID from two parts here
  // to ensure the random number provide enough bits.
  ("000" + ((Math.random() * 46656) | 0).toString(36)).slice(-3) +
  ("000" + ((Math.random() * 46656) | 0).toString(36)).slice(-3)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Rendering Functions

This is a set of functions that make it easier to create HTML bits in a declarative way.
`
)})
    },
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
      name: "style",
      value: (function(){return(
(n,d) => {
  for (var k in d) {n.style[k] = d[k]}
  return n
}
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`The \`dom\` object contains a collection of functions to easily create and manipulate DOM elements.`
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
      name: "svg",
      inputs: ["dom"],
      value: (function(dom){return(
function(){
  const {namespaces,createns} = dom
  const create = (name,args) => createns(namespaces.svg, name, args)
  return ['altglyph', 'altglyphdef', 'altglyphitem', 'animate', 'animatecolor', 'animatemotion', 'animatetransform', 'circle', 'clippath', 'colorProfile', 'cursor', 'defs', 'desc', 'ellipse', 'feblend', 'fecolormatrix', 'fecomponenttransfer', 'fecomposite', 'feconvolvematrix', 'fediffuselighting', 'fedisplacementmap', 'fedistantlight', 'feflood', 'fefunca', 'fefuncb', 'fefuncg', 'fefuncr', 'fegaussianblur', 'feimage', 'femerge', 'femergenode', 'femorphology', 'feoffset', 'fepointlight', 'fespecularlighting', 'fespotlight', 'fetile', 'feturbulence', 'filter', 'font', 'fontFace', 'fontFaceFormat', 'fontFaceName', 'fontFaceSrc', 'fontFaceUri', 'foreignobject', 'g', 'glyph', 'glyphref', 'hkern', 'image', 'line', 'lineargradient', 'marker', 'mask', 'metadata', 'missingGlyph', 'mpath', 'path', 'pattern', 'polygon', 'polyline', 'radialgradient', 'rect', 'script', 'set', 'stop', 'style', 'svg', 'symbol', 'text', 'textpath', 'title', 'tref', 'tspan', 'use', 'view', 'vkern'].reduce((r,k) => {
    r[k] = (...args) => create(k, args);return r
  }, {...dom})
}()
)})
    },
    {
      name: "showhide",
      inputs: ["show","hide"],
      value: (function(show,hide){return(
(node, value) => value ? show(node) : hide(node)
)})
    },
    {
      name: "hide",
      inputs: ["swallow"],
      value: (function(swallow){return(
node => swallow(node.classList.add("hidden"), node)
)})
    },
    {
      name: "show",
      inputs: ["swallow"],
      value: (function(swallow){return(
node => swallow(node.classList.remove("hidden"), node)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`The \`setattr(node,name,value,append?)\` can set DOM node attributes with multiple types of \`value\`, while also managing \`style\` properties passed as values.`
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
      name: "Empty",
      value: (function(){return(
"\u200b"
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`### Slots

`
)})
    },
    {
      name: "slot",
      inputs: ["Slot"],
      value: (function(Slot){return(
(view,value) => 
  new Slot(view,value)
)})
    },
    {
      name: "Slot",
      inputs: ["callable","map","each","html","list"],
      value: (function(callable,map,each,html,list){return(
class Slot {
  constructor( value ) {
    this.value = value;
    this.views = [];
    this.effects = [];
  }
  reduce( ...slots ) {
    const functor = callable(this.value);
    const inputs  = slots;
    const updater = () =>
      this.set(functor(...(map(inputs, _ => _.value)), this.value))
    this.value = undefined;
    // NOTE: This will leak
    each(inputs, _ => _.effect(updater));
    updater();
    return this;
  }
  set( value ) {
    const previous = this.value;
    this.value = value;
    this.views.forEach( view => {
      view.content = html.remount(view.node, view.render(value, previous), view.content)
    })
    this.effects.forEach( effect => effect(value, previous) );
  }
 effect( effector ) {
   this.effects.push(effector);
 }
 view( render ) {
   if (!render) {return undefined};
   const node = document.createComment("view");
   const view = {node, render:render, content:render(this.value, undefined)}
   this.views.push(view)
   return [node].concat(list(view.content));
 }
}
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## DOM Manipulation`
)})
    },
    {
      name: "withClass",
      inputs: ["each"],
      value: (function(each){return(
(classname, scope=document.body) => {
  const res = scope.classList.contains(classname) ? [scope] : [];
  each(scope.querySelectorAll, _ => res.push(_))
  return res;
}
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Event Handling

- <code>on(node,handlers)</code> binds the given map of event handlers <code>{EVENT:Function}</code> to the given *node*
- <code>off(node,handlers)</code> *un*binds the given map of event handlers <code>{EVENT:Function}</code> to the given *node*`
)})
    },
    {
      name: "on",
      inputs: ["list"],
      value: (function(list){return(
(node, handlers) =>
  Object.entries(handlers).forEach(([k, v]) =>
    list(node).forEach((_) => _.addEventListener(k, v))
  ) || node
)})
    },
    {
      name: "off",
      inputs: ["list"],
      value: (function(list){return(
(node,handlers) => Object.entries(handlers).forEach( ([k,v]) => list(node).forEach(_ => _.removeEventListener(k,v)) ) || node
)})
    },
    {
      name: "keymap",
      inputs: ["swallow"],
      value: (function(swallow){return(
(node, keys) => swallow(
  node.addEventListener("keydown", _ => keys[_.key] ? keys[_.key](_, "down"): undefined),
  node
)
)})
    },
    {
      name: "bind",
      value: (function(){return(
(scope,key,handler) => {
  if (scope[key]) {scope[key].push(handler)}
  else {scope[key]=[handler]}
  return scope;
}
)})
    },
    {
      name: "unbind",
      value: (function(){return(
(scope,key,handler) => {
  if (scope[key]) {scope[key]=scope[key].filter(_ => _ !== handler)}
  return scope;
}
)})
    },
    {
      name: "trigger",
      value: (function(){return(
(scope, key, ...value) =>
  scope && scope[key] &&
  scope[key].forEach(_ => _(...value))
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`# Time & Async`
)})
    },
    {
      name: "ms",
      inputs: ["idem"],
      value: (function(idem){return(
idem
)})
    },
    {
      name: "s",
      inputs: ["ms"],
      value: (function(ms){return(
_ => ms(_ * 1000)
)})
    },
    {
      name: "m",
      inputs: ["s"],
      value: (function(s){return(
_ => s(_ * 60)
)})
    },
    {
      name: "defer",
      value: (function(){return(
(effector, delay=0, guard=undefined) => delay ? window.setTimeout(guard ? _ => (guard() && effector(effector)) : effector, delay) : effector(effector)
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
      name: "now",
      value: (function(){return(
window.performance.now
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`# Formatting`
)})
    },
    {
      name: "sprintf",
      value: (function(){return(
(...args)=>{
    var str_repeat  = function(i, m){ for (var o = []; m > 0; o[--m] = i) {}; return(o.join(''));};
		var i = 0, a, f = args[i++], o = [], m, p, c, x;
		while (f) {
			if (m = /^[^\x25]+/.exec(f)) {
				o.push(m[0]);
			} else if (m = /^\x25{2}/.exec(f)) {
				o.push('%');
			} else if (m = /^\x25(?:(\d+)\$)?(\+)?(0|'[^$])?(-)?(\d+)?(?:\.(\d+))?([b-fosuxX])/.exec(f)) {
				if (((a = args[m[1] || i++]) == null) || (a == undefined)) {
					return console.error("std.core.sprintf: too few arguments, expected ", args.length, "got", i - 1, "in", args[0]);
				}
				if (/[^s]/.test(m[7]) && (typeof(a) != 'number')) {
					return console.error("std.core.sprintf: expected number at", i - 1, "got",a, "in", args[0]);
				}
				switch (m[7]) {
					case 'b': a = a.toString(2); break;
					case 'c': a = String.fromCharCode(a); break;
					case 'd': a = parseInt(a); break;
					case 'e': a = m[6] ? a.toExponential(m[6]) : a.toExponential(); break;
					case 'f': a = m[6] ? parseFloat(a).toFixed(m[6]) : parseFloat(a); break;
					case 'o': a = a.toString(8); break;
					case 's': a = ((a = String(a)) && m[6] ? a.substring(0, m[6]) : a); break;
					case 'u': a = Math.abs(a); break;
					case 'x': a = a.toString(16); break;
					case 'X': a = a.toString(16).toUpperCase(); break;
				}
				a = (/[def]/.test(m[7]) && m[2] && a > 0 ? '+' + a : a);
				c = m[3] ? m[3] == '0' ? '0' : m[3].charAt(1) : ' ';
				x = m[5] - String(a).length;
				p = m[5] ? str_repeat(c, x) : '';
				o.push(m[4] ? a + p : p + a);
			} else {
				return console.error("std.core.sprintf: reached state that shouldn't have been reached.");
			}
			f = f.substring(m[0].length);
		}
		return o.join('');
}
)})
    },
    {
      inputs: ["sprintf"],
      value: (function(sprintf){return(
sprintf("%0.2f%%", 0.12232 * 100)
)})
    },
    {
      inputs: ["md"],
      value: (function(md){return(
md`## Hashing`
)})
    },
    {
      name: "strhash",
      value: (function(){return(
(text, seed = 5381) => {
  let hash = 5381,
    i = text.length;
  while (i) {
    hash = (hash * 33) ^ text.charCodeAt(--i);
  }
  return hash >>> 0;
}
)})
    },
    {
      name: "numcode",
      value: (function(){return(
(
  number,
  alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
) => {
  const res = [];
  const n = alphabet.length;
  let v = number;
  while (v > 0) {
    const r = v % n;
    v = Math.floor(v / n);
    res.unshift(alphabet.charAt(r));
  }
  return res.join("");
}
)})
    },
    {
      name: "md5",
      value: (function(){return(
(inputString) => {
  var hc = "0123456789abcdef";
  function rh(n) {
    var j,
      s = "";
    for (j = 0; j <= 3; j++)
      s +=
        hc.charAt((n >> (j * 8 + 4)) & 0x0f) + hc.charAt((n >> (j * 8)) & 0x0f);
    return s;
  }
  function ad(x, y) {
    var l = (x & 0xffff) + (y & 0xffff);
    var m = (x >> 16) + (y >> 16) + (l >> 16);
    return (m << 16) | (l & 0xffff);
  }
  function rl(n, c) {
    return (n << c) | (n >>> (32 - c));
  }
  function cm(q, a, b, x, s, t) {
    return ad(rl(ad(ad(a, q), ad(x, t)), s), b);
  }
  function ff(a, b, c, d, x, s, t) {
    return cm((b & c) | (~b & d), a, b, x, s, t);
  }
  function gg(a, b, c, d, x, s, t) {
    return cm((b & d) | (c & ~d), a, b, x, s, t);
  }
  function hh(a, b, c, d, x, s, t) {
    return cm(b ^ c ^ d, a, b, x, s, t);
  }
  function ii(a, b, c, d, x, s, t) {
    return cm(c ^ (b | ~d), a, b, x, s, t);
  }
  function sb(x) {
    var i;
    var nblk = ((x.length + 8) >> 6) + 1;
    var blks = new Array(nblk * 16);
    for (i = 0; i < nblk * 16; i++) blks[i] = 0;
    for (i = 0; i < x.length; i++)
      blks[i >> 2] |= x.charCodeAt(i) << ((i % 4) * 8);
    blks[i >> 2] |= 0x80 << ((i % 4) * 8);
    blks[nblk * 16 - 2] = x.length * 8;
    return blks;
  }
  var i,
    x = sb(inputString),
    a = 1732584193,
    b = -271733879,
    c = -1732584194,
    d = 271733878,
    olda,
    oldb,
    oldc,
    oldd;
  for (i = 0; i < x.length; i += 16) {
    olda = a;
    oldb = b;
    oldc = c;
    oldd = d;
    a = ff(a, b, c, d, x[i + 0], 7, -680876936);
    d = ff(d, a, b, c, x[i + 1], 12, -389564586);
    c = ff(c, d, a, b, x[i + 2], 17, 606105819);
    b = ff(b, c, d, a, x[i + 3], 22, -1044525330);
    a = ff(a, b, c, d, x[i + 4], 7, -176418897);
    d = ff(d, a, b, c, x[i + 5], 12, 1200080426);
    c = ff(c, d, a, b, x[i + 6], 17, -1473231341);
    b = ff(b, c, d, a, x[i + 7], 22, -45705983);
    a = ff(a, b, c, d, x[i + 8], 7, 1770035416);
    d = ff(d, a, b, c, x[i + 9], 12, -1958414417);
    c = ff(c, d, a, b, x[i + 10], 17, -42063);
    b = ff(b, c, d, a, x[i + 11], 22, -1990404162);
    a = ff(a, b, c, d, x[i + 12], 7, 1804603682);
    d = ff(d, a, b, c, x[i + 13], 12, -40341101);
    c = ff(c, d, a, b, x[i + 14], 17, -1502002290);
    b = ff(b, c, d, a, x[i + 15], 22, 1236535329);
    a = gg(a, b, c, d, x[i + 1], 5, -165796510);
    d = gg(d, a, b, c, x[i + 6], 9, -1069501632);
    c = gg(c, d, a, b, x[i + 11], 14, 643717713);
    b = gg(b, c, d, a, x[i + 0], 20, -373897302);
    a = gg(a, b, c, d, x[i + 5], 5, -701558691);
    d = gg(d, a, b, c, x[i + 10], 9, 38016083);
    c = gg(c, d, a, b, x[i + 15], 14, -660478335);
    b = gg(b, c, d, a, x[i + 4], 20, -405537848);
    a = gg(a, b, c, d, x[i + 9], 5, 568446438);
    d = gg(d, a, b, c, x[i + 14], 9, -1019803690);
    c = gg(c, d, a, b, x[i + 3], 14, -187363961);
    b = gg(b, c, d, a, x[i + 8], 20, 1163531501);
    a = gg(a, b, c, d, x[i + 13], 5, -1444681467);
    d = gg(d, a, b, c, x[i + 2], 9, -51403784);
    c = gg(c, d, a, b, x[i + 7], 14, 1735328473);
    b = gg(b, c, d, a, x[i + 12], 20, -1926607734);
    a = hh(a, b, c, d, x[i + 5], 4, -378558);
    d = hh(d, a, b, c, x[i + 8], 11, -2022574463);
    c = hh(c, d, a, b, x[i + 11], 16, 1839030562);
    b = hh(b, c, d, a, x[i + 14], 23, -35309556);
    a = hh(a, b, c, d, x[i + 1], 4, -1530992060);
    d = hh(d, a, b, c, x[i + 4], 11, 1272893353);
    c = hh(c, d, a, b, x[i + 7], 16, -155497632);
    b = hh(b, c, d, a, x[i + 10], 23, -1094730640);
    a = hh(a, b, c, d, x[i + 13], 4, 681279174);
    d = hh(d, a, b, c, x[i + 0], 11, -358537222);
    c = hh(c, d, a, b, x[i + 3], 16, -722521979);
    b = hh(b, c, d, a, x[i + 6], 23, 76029189);
    a = hh(a, b, c, d, x[i + 9], 4, -640364487);
    d = hh(d, a, b, c, x[i + 12], 11, -421815835);
    c = hh(c, d, a, b, x[i + 15], 16, 530742520);
    b = hh(b, c, d, a, x[i + 2], 23, -995338651);
    a = ii(a, b, c, d, x[i + 0], 6, -198630844);
    d = ii(d, a, b, c, x[i + 7], 10, 1126891415);
    c = ii(c, d, a, b, x[i + 14], 15, -1416354905);
    b = ii(b, c, d, a, x[i + 5], 21, -57434055);
    a = ii(a, b, c, d, x[i + 12], 6, 1700485571);
    d = ii(d, a, b, c, x[i + 3], 10, -1894986606);
    c = ii(c, d, a, b, x[i + 10], 15, -1051523);
    b = ii(b, c, d, a, x[i + 1], 21, -2054922799);
    a = ii(a, b, c, d, x[i + 8], 6, 1873313359);
    d = ii(d, a, b, c, x[i + 15], 10, -30611744);
    c = ii(c, d, a, b, x[i + 6], 15, -1560198380);
    b = ii(b, c, d, a, x[i + 13], 21, 1309151649);
    a = ii(a, b, c, d, x[i + 4], 6, -145523070);
    d = ii(d, a, b, c, x[i + 11], 10, -1120210379);
    c = ii(c, d, a, b, x[i + 2], 15, 718787259);
    b = ii(b, c, d, a, x[i + 9], 21, -343485551);
    a = ad(a, olda);
    b = ad(b, oldb);
    c = ad(c, oldc);
    d = ad(d, oldd);
  }
  return rh(a) + rh(b) + rh(c) + rh(d);
}
)})
    }
  ]
};

const notebook = {
  id: "28e219d819b6b627@2228",
  modules: [m0]
};

export default notebook;
