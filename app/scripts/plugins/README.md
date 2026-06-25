# Script Plugins

Drop Python script plugins in this directory. A plugin can expose either:

```python
SCRIPT = ScriptDefinition(...)
```

or:

```python
def register(registry):
    registry.register(ScriptDefinition(...))
```

The GUI reads each script's schema and builds the parameter form automatically.
