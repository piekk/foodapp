// Get Value of product category and show related form


let pTitle = document.getElementById('producttitle');
let i = document.getElementById('add-image');
let cat = document.getElementById('category');
let catdisplay = document.getElementById('category-detail');
let titledisplay = document.getElementById('product-title');


let titleerror = document.getElementById('titleError')


let selectedField = document.getElementById("category");

let categoryButton = document.getElementById('confirm-category');
let addImageButton = document.getElementById('confirm-image');
let addPriceButton = document.getElementById('price-setting');

let setPrice = document.getElementById('setprice');

let description_details = document.getElementById('description_details');


function addImage() {
  if (pTitle.value == '') {
    titleerror.innerHTML = "คุณไม่ได้ระบุชื่อสินค้า";
    titleerror.style.display = 'block';
  } else {
    let category = selectedField.options[selectedField.selectedIndex].value;
    let c = selectedField.options[selectedField.selectedIndex].innerText;
    titleerror.style.display = 'none';
    i.style.display = 'block';
    categoryButton.style.display = 'none';
    cat.style.display = 'none';
    catdisplay.innerHTML = c;
    pTitle.style.display = 'none';
    titledisplay.innerHTML = pTitle.value;
    addImageButton.style.display = 'block';
  }
}

function addDescription() {
  let category = selectedField.options[selectedField.selectedIndex].value;
  description_details.style.display ='block'
  addImageButton.style.display = 'none';
  addPriceButton.style.display = 'block';
}

function toSetPrice() {
  let category = selectedField.options[selectedField.selectedIndex].value;
  addPriceButton.style.display = 'none';
  setPrice.style.display = 'block';
}

function checkPrice() {
  let pbutton = document.getElementById('price-show');
  let prdisplay = Number(document.getElementById('pr-set').value);
  let shipdisplay = Number(document.getElementById('ship-set').value);
  let psum = document.getElementById('price-sum')
  let pshow = document.getElementById('pr-show')
  let mget = document.getElementById('merchant-gets')
  let priceerror = document.getElementById('PriceError')
  let shippingfeeerror = document.getElementById('ShippingFeeError')
  //ดึงราคามาร์คอัพ
  let mark = document.getElementById('auto-mark-noshow');
  //ส่่วนลดสินค้า
  let discounted = document.getElementById('discount-set')
  let discount_percent = Number(discounted.value / 100)
  //ราคาแสดงบนเวป
  let totalpr = Math.round(((prdisplay * (1-discount_percent))*mark.innerHTML) + shipdisplay);
  let sellerget = Math.round((prdisplay * (1-discount_percent)) + shipdisplay)
  psum.style.display = 'block';
  if(isNaN(prdisplay)){
    priceerror.style.display = 'block';
  }
  else{
    pshow.innerHTML = "ราคาที่แสดงบนเวปไซต์" + " : ฿ " + String(totalpr) + ".00";
    mget.innerHTML = "จำนวนเงินที่คุณได้รับ" + " : ฿ " + String(sellerget)+ ".00";
  }
}
