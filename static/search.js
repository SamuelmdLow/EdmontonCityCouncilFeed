function search()
{
    term = document.getElementById("input").value;
    term = term.replace(".", "");
    window.location.href = "/search/" + term;
}