function toggle(that)
{
    //alert(that.nextSibling.nodeName);
    sib = that.nextSibling.classList;
    sib.toggle("hidden");

    //alert(sib[1]);
    if (sib[sib.length - 1] == "hidden")
    {
        that.src = "https://upload.wikimedia.org/wikipedia/commons/3/32/VisualEditor_-_Icon_-_Collapse.svg";
    }
    else
    {
        that.src = "https://upload.wikimedia.org/wikipedia/commons/2/2f/VisualEditor_-_Icon_-_Expand.svg";
    }
}