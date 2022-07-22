function toggle(that)
{
    //alert(that.nextSibling.nodeName);
    sib = that.nextSibling.classList;
    sib.toggle("hidden");

    //alert(sib[1]);
    if (sib[sib.length - 1] == "hidden")
    {
        that.innerHTML = "-";
    }
    else
    {
        that.innerHTML = "+";
    }
}