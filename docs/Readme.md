Run apidoc to collect all classes:
```
sphinx-apidoc -f -o source/ ../src/ ../src/run.py ../src/debug.py
```

Run make to actually create the documentation
```
make html
```