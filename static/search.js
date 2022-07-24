function search()
{
    term = document.getElementById("input").value;
    window.location.href = "/search/" + term;
}