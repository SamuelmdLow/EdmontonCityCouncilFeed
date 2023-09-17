# Edmonton City Council Feed

## Goal 1 (met)
Parse information from an edmonton city council escribe meeting
(ex. https://pub-edmonton.escribemeetings.com/Meeting.aspx?Agenda=PostMinutes&Id=90d0b4a6-47d2-47f1-a735-9076e5a89c0f&Item=19&Tab=attachments&lang=English)

### Example of HTML
```
<li class="AgendaItemMotion">

    <div class="PreMotionText RichText"></div>
    
    <div class="Number"></div>
    
    <div class="MovedBy">
        <span class="Label">Moved by:</span>
        <span class="Value">A. Salvador</span>
    </div>
    
    <div class="SecondedBy">
        <span class="Label">Seconded by:</span>
        <span class="Value">A. Sohi</span>
    </div>
    
    <div class="MotionText RichText">
        <p><span style="font-weight:400;"><span><strong>Bylaw 20071 - Temporary Transit and City Facilities Face Mask Bylaw</strong></span></span></p>
        <p><span style="font-weight:400;">That Administration prepare a new Face Mask Bylaw to only include provisions for face coverings on public transit and publicly accessible City-owned and operated facilities.</span></p>
        <p><strong>Due Date: March 14/16, 2022, City Council</strong></p>
    </div>
    
    <table class="MotionVoters"><tbody>
        <tr>
            <td class="VoterVote" colspan="1" headers="">In Favour (11)</td>
            <td class="VotesUsers" colspan="1" headers="">A. Knack, S. Hamilton, A. Paquette, T. Cartmell, A. Sohi, A. Salvador, M. Janz, K. Tang, E. Rutherford, A. Stevenson, and J. Wright</td>
        </tr>
        <tr>
            <td class="VoterVote" colspan="1" headers="">Opposed (2)</td>
            <td class="VotesUsers" colspan="1" headers="">J. Rice, and K. Principe</td>
        </tr>
        <tr>
            <td class="VotesUsers" colspan="1" headers=""></td>
        </tr>
    </tbody></table>
    
    <div class="MotionResult">
        Motion Carried (11 to 2)
    </div>
    
    <div class="PostMotionText RichText"></div>
</li>
```

### Plan
1. Create a function for getting the values of elements
2. Create recursive function which organizes element into array of structure
```
[ "class name"
    [ "class name"
        [ "class name", value ]
    ],
    
    [ "class name", value ],

    [ "class name"
        [ "class name"
            [ "class name", value ]
        ]
    ]
]
```
3. Create an object for AgendaItems
4. Get html of webpage
5. Get all elements of class "AgendaItemMotion"
6. Remove all elements that include "boring" terms
7. Output information in all AgendaItems in text form

## Goal 2 (met)
Send requests for json files from their webserver

### Plan
1. Figure it out 💀 

## Goal 3 (met)
Create the website

## Goal 4 (met)
Create an RSS feed for the information

## Goal 5 (met)
Create a mastodon bot for the information
