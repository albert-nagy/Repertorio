var select1;
var select2;

function authOperation(result)
  {
  var response = JSON.parse(result);
  if (response[0] == 0)
    window.location.href = page;
  else if (response[0] == 1)
    return response[1];
  } 

function getForm(what, id) {
  $.ajax({
      type: 'POST',
      url: '/infotoedit?what='+what+'&id='+id,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,1);}
      
  }); 
  }

function editContent(form, what, id) {
  var content;
  if (what == 'bio')
    content = '&text='+encodeURIComponent(form.elements['edit_bio'].value);
  else if (what == 'contact')
    content = '&phone='+encodeURIComponent(form.elements['phone'].value)+'&address='+encodeURIComponent(form.elements['address'].value);
  else if (what == 'email_privacy')
    content = '';

  $.ajax({
      type: 'POST',
      url: '/edit?action=edit&what='+what+'&id='+id+content,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,0);}
  }); 
  }

  function Cancel(what,id) {
  $.ajax({
      type: 'POST',
      url: '/edit?action=cancel&what='+what+'&id='+id,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,0);}
  }); 
  }

  function addWork(form,id)
    {
    var composer = form.elements['composer'].value.trim();
    var title = form.elements['title'].value.trim();
    var duration = form.elements['duration'].value.trim();
    var category;
    if (document.getElementById('category'))
      {
      var select = document.getElementById('category');
      category = encodeURIComponent(select.options[select.selectedIndex].value);
      }
    else
      category = encodeURIComponent(form.elements['category'].value.trim());
    var instrument;
    if (document.getElementById('instrument'))
      {
      var select = document.getElementById('instrument');
      instrument = encodeURIComponent(select.options[select.selectedIndex].value);
      }
    else
      instrument = encodeURIComponent(form.elements['instrument'].value.trim());
    
    if (!composer||!title||!duration||!category||!instrument)
      alert("Please fill out all fields!");
    else if (isNaN(duration)||Math.round(duration)<1)
      alert("Duration has to be a number greater than 0!");
    else
      {
      var content = '&composer='+encodeURIComponent(composer)+'&title='+encodeURIComponent(title)+
      '&duration='+Math.round(duration)+'&category='+category+'&instrument='+instrument;
      $.ajax({
        type: 'POST',
        url: '/add_work?id='+id+content,
        contentType: 'application/octet-stream; charset=utf-8',
        success: function(result) {replacePart('repertoire',result,id,0);}
      });
      }
    }

  function replacePart(what,result,id,form)
    {
    if (what != 'cat_selector')
      var response = authOperation(result);
    var text;
    if (what == 'bio')
      {
      if (form == 0)
        text = `<p>`+response+`</p>
          <button type="submit" class="edit" onclick="getForm('bio', '`+id+`');">Edit Bio</button>`;
      else
        text = `<form action="javascript:void(0)" method="post" onsubmit="editContent(this, 'bio', '`+id+`')">
                <textarea name="edit_bio">`+response+`</textarea>
                <button type="submit" class="edit">Save</button>
                <button type="reset" class="cancel" onclick="Cancel('bio','`+id+`')">Cancel</button>
                </form>`;
      }
    else if (what == 'contact')
      {
      var phone = (response[0] != null) ? response[0]:``;
      var address = (response[1] != null) ? response[1]:``;
      if (form == 1)
        {
        text = `<form action="javascript:void(0)" method="post" onsubmit="editContent(this, 'contact', '`+id+`')">
                <p><label><strong>Phone: </strong><input type="text" name="phone" value="`+phone+`" /></label></p>
                <p><label><strong>Address: </strong><input type="text" name="address" value="`+address+`" /></label></p>
                <button type="submit" class="edit">Save</button>
                <button type="reset" class="cancel" onclick="Cancel('contact','`+id+`')">Cancel</button>
                </form>`;
        }
      else
        {
        if (phone == ``)
          phone = `-`;
        if (address == ``)
          address = `-`;
        text = `<p><strong>Phone: </strong>`+phone+`</p>
                <p><strong>Address: </strong>`+address+`</p>
                <button type="submit" class="edit" onclick="getForm('contact','`+id+`');">Edit Contact Info</button>`
        }
      }
    else if (what == 'email_privacy')
      text = response;
    else if (what == 'add_work')
      {
      if (form == 1)
        text = response;
      else
        text = `<button class="add" onclick="getForm('add_work','`+id+`');">+ Add Work to your Repertoire</button>`;
      }
    else if (what == 'repertoire')
      {
      document.getElementById('instruments').innerHTML = response[0]; 
      text = response[1];
      }
    else if (what == 'cat_selector')
      {
        if (result == 0)
        {
        select1 = document.getElementById('cat_selector').innerHTML;
        text = `<strong>Create Category: </strong>
          <input type="text" name="category" value="" /> 
          <button type="button" onclick="replacePart('cat_selector',1,0,0)">Select an existing category instead</button>`; 
        }
        else
          text = select1;
      }
    else if (what == 'inst_selector')
      {
        if (result == 0)
        {
        select2 = document.getElementById('inst_selector').innerHTML;
        text = `<strong>Create Instrument: </strong>
          <input type="text" name="instrument" value="" /> 
          <button type="button" onclick="replacePart('inst_selector',1,0,0)">Select an instrument from the list</button>`; 
        }
        else
          text = select2;      
      }
    document.getElementById(what).innerHTML = text;
    }

function delWork(work,id)
 {
  if (confirm("Are you sure to delete this work?"))
  {
  $.ajax({
        type: 'POST',
        url: '/del_work?id='+id+'&work='+work,
        contentType: 'application/octet-stream; charset=utf-8',
        success: function(result) {replacePart('repertoire',result,id,0);}
      });

  }
 }