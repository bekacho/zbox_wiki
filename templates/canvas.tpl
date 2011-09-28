$def with (title, content, static_files=None, toolbox=True, quicklinks=True)
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="utf-8" />
    <title>$title</title>

    <style type="text/css">
        #searchbox { float : right; }
        hr { clear : both; }
    </style>

$if static_files:
    $static_files

</head>
<body>


$if quicklinks:
    <div id="quicklinks">
        <a href="/">Recnet Changes</a>
        <a href="/~index">Index</a>
    </div>

    <div id="searchbox">
        <div id="form">
            <form method="POST" action="/~s" accept-charset="utf-8">
                <input type="text" name="k" />
                <input type="submit" value="Search" />
            </form>
        </div>
    </div>

    <hr />


<div id="title">$title</div>
<hr />

<div id="content">$content</div>
<hr />

$if toolbox:
    <div id="toolbox">
    <a href="/$title?action=delete">Delete</a>
    <a href="/$title?action=rename">Rename</a>
    <a href="/$title?action=edit">Edit</a>
    </div>


</body>
</html>