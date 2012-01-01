$def with (conf, req_path, title, content, static_files=None, toolbox=True, quicklinks=True)
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>$req_path</title>

    $if static_files:
        $static_files

</head>
<body>


<div id="container">

$if quicklinks:
    <div id="quicklinks">
        <a href="/">Recent Changes</a>
        <a href="/~index">Index</a>
    </div>

    <div id="searchbox">
        <form method="POST" action="/~s" accept-charset="utf-8">
            <input type="text" name="k" class="auto-increase-width-size" />
            <input type="submit" value="Search" />
        </form>
    </div>


<div id="title">$title</div>

<div id="content">$content</div>


$if toolbox:
    <div id="toolbox">
        <a href="/$req_path?action=source">Source</a>

        $if not conf.readonly:
            <a href="/$req_path?action=delete">Delete</a>
            <a href="/$req_path?action=rename">Rename</a>
            <a href="/$req_path?action=edit">Edit</a>
        $else:
            <span>Delete</span>
            <span>Rename</span>
            <span>Edit</span>
    </div>


</div>


$if conf.maintenance_email:
    $ email = conf.maintenance_email_prefix + '<span class="hide">null</span>@' + conf.maintenance_email_suffix
    <footer>
        <p>
            $email
        </p>
    </footer>

</body>
</html>
