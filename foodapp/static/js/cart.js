//Update total price in cart.html
window.addEventListener('load', function() {
    let num = document.getElementsByClassName('productname');
    let dicNum = {};
    let tamount = document.getElementById('t_amount');
    let t = 0;
    for (var i=0; i<num.length; i++){
      // load order for item from db
      // order = no[1] will give  eg: "the food name"
      let order = document.getElementById('no'+num[i].innerText);
      // load price from db
      let price = document.getElementById('price'+num[i].innerText);
      let totalPrice = document.getElementById('totalPrice'+num[i].innerText);
      // create array of itemname and quantity
      dicNum[num[i].innerText] = order.innerText;

      //update select field equal to order from db
      let e = document.getElementById(num[i].innerText);
      e.value = dicNum[num[i].innerText];
      //display total price from selected field and price
      var n = price.innerText * e.value;
      t += Number(totalPrice.innerText);
      totalPrice.innerText = n.toLocaleString();
      tamount.innerText = t.toLocaleString();
    }
})



// Update product quantity
function getVal(){
  let p = document.getElementsByClassName('productname');
  let quantity = {};
  let tamount = document.getElementById('t_amount');
  let t = 0;
  for (var i = 0; i<p.length; i++){
    let q = document.getElementById(p[i].innerText);
    let price = document.getElementById('price'+p[i].innerText);
    let totalPrice = document.getElementById('totalPrice'+p[i].innerText);
    let realQ = q.selectedIndex+1;
    quantity[p[i].innerText] = realQ;
    var n = price.innerText * quantity[p[i].innerText]
    t += Number(n);
    totalPrice.innerText = n.toLocaleString();
    tamount.innerText = t.toLocaleString();
  }
  let quan = JSON.stringify(quantity)
  var xhr = new XMLHttpRequest();
  xhr.open("POST", '/cart/process', true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.send(quan);
  window.location.reload()
}
///let quan = JSON.stringify(quantity)
///var xhr = new XMLHttpRequest();
///xhr.open("POST", '/cart/process', true);
///xhr.setRequestHeader("Content-Type", "application/json");
///xhr.send(quan);
