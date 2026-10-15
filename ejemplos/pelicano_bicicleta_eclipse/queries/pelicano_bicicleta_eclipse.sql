-- Pelícano en bicicleta sobre el río, bajo un eclipse de Sol.
-- Cada píxel se calcula en este SELECT: sin tablas, imágenes de entrada ni UDFs.
-- Ejecución (desde el directorio que contiene queries/ e images/):
-- clickhouse local --output_format_image_width 1600 --output_format_image_height 1000 \
--   --param_SAMPLES 4 --queries-file queries/pelicano_bicicleta_eclipse.sql \
--   > images/pelicano_bicicleta_eclipse.png
-- Coordenadas de diseño: 1600 x 1000; resolución y muestras parametrizadas.
WITH
    getSetting('output_format_image_width')::UInt64 AS W,
    getSetting('output_format_image_height')::UInt64 AS H,
    1600.0 / W AS dx, 1000.0 / H AS dy,
    0.65 * greatest(dx, dy) AS aa,
    (v -> clamp(v, 0.0, 1.0)) AS sat,
    (v -> (toFloat64(bitAnd(bitShiftRight(v,16),255))/255.0,
           toFloat64(bitAnd(bitShiftRight(v,8),255))/255.0,
           toFloat64(bitAnd(v,255))/255.0)) AS rgb,
    ((a,b,t) -> tuplePlus(a,tupleMultiplyByNumber(tupleMinus(b,a),t))) AS mix,
    ((c,t) -> tupleMultiplyByNumber(c,t)) AS mul,
    ((a,b) -> tuplePlus(a,b)) AS add,
    ((x,y) -> sqrt(x*x+y*y)) AS hyp,
    ((ba,bb,bc,bd) -> arrayMap(bt -> (
        pow(1.0-bt/20.0,3)*ba.1+3*pow(1.0-bt/20.0,2)*(bt/20.0)*bb.1+3*(1.0-bt/20.0)*pow(bt/20.0,2)*bc.1+pow(bt/20.0,3)*bd.1,
        pow(1.0-bt/20.0,3)*ba.2+3*pow(1.0-bt/20.0,2)*(bt/20.0)*bb.2+3*(1.0-bt/20.0)*pow(bt/20.0,2)*bc.2+pow(bt/20.0,3)*bd.2
    ),range(21))) AS bez,
    -- Capa: tipo, puntos, elipse, giro, ancho, color, opacidad, caja, relieve.
    ((cx,cy,rx,ry,ang,c) -> (0,[(0.0,0.0)],(cx,cy,rx,ry),ang,0.0,c,1.0,
       (cx-greatest(rx,ry)-4,cy-greatest(rx,ry)-4,cx+greatest(rx,ry)+4,cy+greatest(rx,ry)+4),0.09)) AS ell,
    ((cx,cy,rad,thick,c) -> (3,[(0.0,0.0)],(cx,cy,rad,rad),0.0,thick,c,1.0,
       (cx-rad-thick-4,cy-rad-thick-4,cx+rad+thick+4,cy+rad+thick+4),0.0)) AS ring,
    ((pts,c) -> (1,arrayPushBack(pts,pts[1]),(0.0,0.0,1.0,1.0),0.0,0.0,c,1.0,
       (arrayMin(arrayMap(polygon_pt->polygon_pt.1,pts))-4,arrayMin(arrayMap(polygon_pt->polygon_pt.2,pts))-4,
        arrayMax(arrayMap(polygon_pt->polygon_pt.1,pts))+4,arrayMax(arrayMap(polygon_pt->polygon_pt.2,pts))+4),0.0)) AS poly,
    ((pts,thick,c) -> (2,pts,(0.0,0.0,1.0,1.0),0.0,thick,c,1.0,
       (arrayMin(arrayMap(line_pt->line_pt.1,pts))-thick-4,arrayMin(arrayMap(line_pt->line_pt.2,pts))-thick-4,
        arrayMax(arrayMap(line_pt->line_pt.1,pts))+thick+4,arrayMax(arrayMap(line_pt->line_pt.2,pts))+thick+4),0.0)) AS line,
    ((sp,sa,sb) -> arrayMap(st -> hyp(sp.1-sa.1-st*(sb.1-sa.1),sp.2-sa.2-st*(sb.2-sa.2)),
       [sat(((sp.1-sa.1)*(sb.1-sa.1)+(sp.2-sa.2)*(sb.2-sa.2))/greatest(pow(sb.1-sa.1,2)+pow(sb.2-sa.2,2),0.00001))])[1]) AS seg,
    ((dp,dl) -> multiIf(dl.1=0,
       (hyp(((dp.1-dl.3.1)*cos(dl.4)+(dp.2-dl.3.2)*sin(dl.4))/dl.3.3,
            (-(dp.1-dl.3.1)*sin(dl.4)+(dp.2-dl.3.2)*cos(dl.4))/dl.3.4)-1)*least(dl.3.3,dl.3.4),
       dl.1=3,abs(hyp(dp.1-dl.3.1,dp.2-dl.3.2)-dl.3.3)-dl.5*0.5,
       dl.1=1,if(pointInPolygon(dp,dl.2),-1.0,1.0)*arrayMin(arrayMap(di->seg(dp,dl.2[di],dl.2[di+1]),range(1,length(dl.2)))),
       arrayMin(arrayMap(di->seg(dp,dl.2[di],dl.2[di+1]),range(1,length(dl.2))))-dl.5*0.5)) AS distance,
    ((ip,il) -> mul(il.6,1.0+il.9*clamp((ip.1-il.3.1)/greatest(il.3.3,1.0)*0.35-(ip.2-il.3.2)/greatest(il.3.4,1.0),-1.0,1.0))) AS ink,
    ((pp,pls,pbg) -> arrayFold((pc,pl)->mix(pc,ink(pp,pl),sat(0.5-distance(pp,pl)/aa)*pl.7),
       arrayFilter(pl->pp.1>=pl.8.1 AND pp.2>=pl.8.2 AND pp.1<=pl.8.3 AND pp.2<=pl.8.4,pls),pbg)) AS paint,
    -- Cielo de la totalidad: aureola, corona, disco lunar y perla luminosa.
    (skp -> mix(mix(rgb(0x112d43),rgb(0x577b87),sat(skp.2/550.0)),rgb(0xf0b678),
       0.8*exp(-pow((skp.2-480.0)/175.0,2))*exp(-pow((skp.1-1180.0)/1000.0,2)))) AS sky,
    (ecp -> arrayMap(rad -> arrayMap(ang -> arrayMap(glow ->
       if(rad<74.5,mix(rgb(0x102d3c),rgb(0x203b48),sat(rad/75)*0.22),add(sky(ecp),mul(rgb(0xffdaa2),glow))),
       [0.33*exp(-greatest(rad-77.0,0.0)/40.0)+0.78*exp(-pow((rad-77.0)/2.8,2))
        +0.28*exp(-greatest(rad-78.0,0.0)/65.0)*pow(0.5+0.5*sin(ang*9+1.5*sin(ang*5)),8)
        +0.60*exp(-pow((ecp.1-1294.0)/10.0,2)-pow((ecp.2-388.0)/10.0,2))])[1],
       [atan2(ecp.2-340.0,ecp.1-1235.0)])[1],[hyp(ecp.1-1235.0,ecp.2-340.0)])[1]) AS eclipse,
    (wp -> arrayMap(depth -> arrayMap(band -> arrayMap(reflection ->
       add(mix(rgb(0x528e91),rgb(0x123f52),depth),add(
           mul(rgb(0x357c82),0.09*sin(wp.2*0.115+sin(wp.1*0.012)*2.2)),
           mul(rgb(0xf6bd72),reflection*(0.07+0.20*band)))),
       [exp(-pow((wp.1-1235.0-22*sin(wp.2*0.021))/(24+depth*225),2))])[1],
       [pow(0.5+0.5*sin(wp.2*0.34+sin(wp.1*0.025+wp.2*0.021)*0.7),7)])[1],
       [sat((wp.2-480.0)/520.0)])[1]) AS water,
    [
      poly([(0.,450.),(105.,373.),(192.,410.),(324.,332.),(466.,422.),(572.,382.),(745.,459.),(857.,418.),(997.,474.),(1113.,454.),(1224.,470.),(1364.,443.),(1476.,382.),(1600.,426.),(1600.,540.),(0.,540.)],rgb(0x64848a)),
      poly([(0.,453.),(122.,424.),(241.,455.),(321.,436.),(476.,494.),(609.,465.),(760.,506.),(895.,485.),(1008.,512.),(1135.,491.),(1050.,533.),(903.,557.),(768.,601.),(632.,634.),(465.,674.),(267.,722.),(0.,753.)],rgb(0x2f646c)),
      poly([(0.,555.),(142.,557.),(282.,575.),(400.,557.),(586.,586.),(697.,576.),(818.,561.),(991.,536.),(885.,579.),(735.,614.),(622.,653.),(474.,695.),(353.,758.),(264.,840.),(194.,912.),(146.,1000.),(0.,1000.)],rgb(0x1e4e57)),
      poly([(0.,688.),(165.,687.),(281.,666.),(410.,646.),(522.,649.),(643.,622.),(772.,604.),(646.,650.),(495.,704.),(375.,760.),(272.,852.),(212.,935.),(187.,1000.),(0.,1000.)],rgb(0x173e49)),
      line(bez((174.,994.),(258.,754.),(559.,672.),(796.,595.)),3.,rgb(0x759282)),
      poly([(1361.,491.),(1418.,466.),(1495.,427.),(1554.,446.),(1600.,417.),(1600.,1000.),(1555.,1000.),(1514.,892.),(1519.,775.),(1553.,686.),(1516.,616.),(1455.,573.),(1371.,541.),(1295.,525.)],rgb(0x285b61)),
      poly([(1485.,575.),(1557.,535.),(1600.,554.),(1600.,1000.),(1558.,1000.),(1522.,901.),(1524.,784.),(1566.,679.)],rgb(0x173e49)),
      line(bez((1298.,526.),(1539.,572.),(1602.,659.),(1536.,788.)),3.,rgb(0x789485))
    ] AS banks,
    arrayMap(fi -> arrayMap(xx -> arrayMap(yy -> arrayMap(hh ->
       poly([(xx-9.,yy),(xx-4.,yy-hh*0.30),(xx-8.,yy-hh*0.30),(xx-3.,yy-hh*0.57),(xx-6.,yy-hh*0.57),(xx,yy-hh),
             (xx+6.,yy-hh*0.57),(xx+3.,yy-hh*0.57),(xx+8.,yy-hh*0.30),(xx+4.,yy-hh*0.30),(xx+9.,yy)],rgb(0x295860)),
       [22.+20.*(0.5+0.5*sin(fi*2.7))])[1],[512.+fi*1.7+8.*sin(fi*0.7)])[1],[10.+fi*23.])[1],range(35)) AS forest,
    rgb(0x102f3d) AS dark, rgb(0xf3e9cf) AS ivory,
    rgb(0xb5c7bc) AS feather, rgb(0xef7654) AS coral, rgb(0xf7c66f) AS gold,
    -- Bicicleta de paseo, con radios reales y cuadro de dos triángulos.
    arrayConcat(
      [ring(510.,742.,126.,10.,dark),ring(944.,742.,126.,10.,dark),
       ring(510.,742.,118.5,5.,rgb(0x80b1ab)),ring(944.,742.,118.5,5.,rgb(0x80b1ab))],
      arrayFlatten(arrayMap(cx -> arrayMap(si->line([(cx,742.),(cx+113*cos(si*pi()/10),742.+113*sin(si*pi()/10))],1.6,rgb(0x83a9a3)),range(20)),[510.,944.])),
      [line(bez((399.,714.),(412.,645.),(471.,616.),(534.,622.)),3.,rgb(0xe3d9b0)),
       line(bez((833.,714.),(846.,645.),(905.,616.),(968.,622.)),3.,rgb(0xe3d9b0)),
       line([(698.,729.),(680.,682.)],7.,rgb(0x658b8b)),line([(661.,682.),(699.,682.)],9.,dark),
       line([(706.,538.),(746.,605.),(680.,682.)],17.,rgb(0xbf8c50)),
       poly([(664.,675.),(695.,677.),(704.,686.),(661.,690.),(648.,686.)],rgb(0xd9a35c)),
       line([(510.,742.),(626.,612.),(714.,742.),(510.,742.)],16.,dark),
       line([(626.,612.),(866.,601.),(714.,742.)],17.,dark),line([(866.,601.),(944.,742.)],17.,dark),
       line([(510.,742.),(626.,612.),(714.,742.),(510.,742.)],10.,coral),
       line([(626.,612.),(866.,601.),(714.,742.)],11.,coral),line([(866.,601.),(944.,742.)],10.,coral),
       line([(632.,608.),(856.,597.)],2.7,rgb(0xffcf95)),line([(727.,724.),(865.,606.)],2.2,rgb(0xffc58e)),
       line([(625.,612.),(612.,572.)],10.,dark),line([(624.,605.),(614.,574.)],4.,rgb(0xa5b6a9)),
       line(bez((582.,574.),(606.,565.),(625.,578.),(644.,574.)),17.,dark),
       line(bez((582.,571.),(603.,565.),(626.,573.),(644.,571.)),3.,rgb(0xb58c68)),
       line([(866.,601.),(850.,552.),(899.,543.)],10.,dark),line([(866.,600.),(852.,552.),(899.,545.)],4.,rgb(0xa3b9ac)),
       line(bez((898.,544.),(924.,540.),(929.,561.),(911.,568.)),13.,dark),
       line(bez((899.,543.),(920.,542.),(925.,559.),(911.,563.)),7.,rgb(0xd1bd8b)),
       line(bez((905.,560.),(932.,624.),(891.,637.),(899.,667.)),1.5,dark),
       ell(510.,742.,13.,13.,0.,rgb(0xa1b9ad)),ell(944.,742.,13.,13.,0.,rgb(0xa1b9ad)),
       ell(510.,742.,5.,5.,0.,dark),ell(944.,742.,5.,5.,0.,dark),
       line([(519.,749.),(716.,762.),(735.,731.),(522.,731.)],2.4,rgb(0x72918c)),
       ell(714.,742.,27.,27.,0.,dark),ell(714.,742.,21.,21.,0.,rgb(0xa1b5a4)),ell(714.,742.,16.,16.,0.,rgb(0x345c61)),
       line([(714.,742.),(755.,708.)],8.,rgb(0xc1c5ab)),ell(714.,742.,6.,6.,0.,rgb(0xf6d398)),
       line([(738.,708.),(773.,708.)],10.,dark),line([(743.,705.),(770.,705.)],3.,rgb(0xa6b7a6))]
    ) AS bicycle,
    -- Pelícano: cola, cuerpo, cuello en S, ala, patas y bolsa gular.
    [
      poly(arrayConcat(bez((533.,459.),(498.,467.),(452.,446.),(425.,434.)),bez((425.,434.),(452.,482.),(462.,520.),(534.,534.))),dark),
      poly(arrayConcat(bez((530.,467.),(486.,463.),(463.,451.),(442.,447.)),bez((442.,447.),(470.,480.),(478.,505.),(539.,518.))),rgb(0xd5d9bd)),
      line([(449.,453.),(502.,490.)],3.,rgb(0x8da99e)),line([(462.,474.),(506.,499.)],3.,rgb(0x8da99e)),
      ell(637.,477.,166.,104.,-0.10,dark),ell(637.,474.,161.,100.,-0.10,ivory),
      poly(arrayConcat(bez((497.,495.),(541.,563.),(692.,587.),(763.,515.)),bez((763.,515.),(705.,548.),(575.,536.),(497.,495.))),rgb(0xc8d2bd)),
      poly(arrayConcat(bez((713.,490.),(677.,449.),(707.,372.),(744.,316.)),bez((744.,316.),(765.,284.),(791.,252.),(828.,246.)),
         bez((828.,246.),(871.,240.),(888.,276.),(867.,305.)),bez((867.,305.),(826.,333.),(794.,341.),(794.,394.)),
         bez((794.,394.),(799.,437.),(817.,473.),(775.,522.)),bez((775.,522.),(749.,547.),(712.,525.),(713.,490.))),dark),
      poly(arrayConcat(bez((716.,488.),(684.,448.),(712.,375.),(748.,319.)),bez((748.,319.),(770.,284.),(794.,257.),(829.,251.)),
         bez((829.,251.),(867.,247.),(882.,276.),(863.,302.)),bez((863.,302.),(822.,329.),(789.,342.),(789.,394.)),
         bez((789.,394.),(793.,440.),(812.,473.),(771.,518.)),bez((771.,518.),(748.,539.),(716.,522.),(716.,488.))),ivory),
      poly(arrayConcat(bez((774.,313.),(733.,369.),(718.,426.),(744.,473.)),bez((744.,473.),(755.,492.),(755.,507.),(745.,521.)),
         bez((745.,521.),(713.,492.),(710.,453.),(718.,417.)),bez((718.,417.),(727.,373.),(752.,335.),(774.,313.))),rgb(0xc1cec0)),
      line(bez((763.,329.),(728.,390.),(723.,419.),(735.,449.)),2.8,rgb(0xe2ddbf)),
      poly(arrayConcat(bez((525.,450.),(587.,413.),(674.,439.),(723.,503.)),bez((723.,503.),(727.,541.),(591.,553.),(525.,503.)),
         bez((525.,503.),(505.,486.),(506.,466.),(525.,450.))),rgb(0x6e9190)),
      poly(arrayConcat(bez((528.,451.),(587.,428.),(651.,449.),(689.,478.)),bez((689.,478.),(655.,494.),(580.,495.),(528.,473.))),rgb(0xd9ddc6)),
      poly(arrayConcat(bez((528.,476.),(579.,500.),(656.,495.),(708.,506.)),bez((708.,506.),(668.,526.),(574.,528.),(533.,496.))),rgb(0xb5c7b8)),
      line(bez((548.,484.),(589.,505.),(644.,506.),(686.,506.)),3.,rgb(0x7b9b94)),
      line(bez((554.,497.),(598.,521.),(654.,515.),(692.,516.)),3.,rgb(0x638b87)),
      line(bez((576.,515.),(619.,535.),(662.,524.),(699.,523.)),3.,rgb(0x466f72)),
      line(bez((591.,528.),(631.,540.),(670.,531.),(704.,529.)),3.,rgb(0x466f72)),
      -- Ala que sujeta el manillar.
      poly(arrayConcat(bez((748.,451.),(775.,486.),(821.,527.),(887.,542.)),bez((887.,542.),(900.,547.),(900.,560.),(883.,563.)),
         bez((883.,563.),(821.,561.),(768.,529.),(736.,498.))),dark),
      poly(arrayConcat(bez((750.,458.),(783.,496.),(824.,532.),(885.,547.)),bez((885.,547.),(894.,550.),(894.,556.),(881.,557.)),
         bez((881.,557.),(824.,555.),(772.,525.),(741.,495.))),rgb(0xdce0c7)),
      line(bez((769.,498.),(805.,533.),(846.,547.),(875.,552.)),3.,rgb(0x90aca1)),line([(881.,546.),(888.,556.)],4.,rgb(0x547a79)),
      line([(675.,545.),(652.,611.),(752.,698.)],21.,dark),line([(675.,545.),(652.,611.),(752.,698.)],14.,gold),
      line([(675.,548.),(656.,609.),(755.,696.)],3.,rgb(0xffdf98)),
      poly([(742.,687.),(755.,685.),(768.,694.),(786.,700.),(780.,707.),(754.,705.),(736.,702.)],dark),
      poly([(745.,689.),(756.,688.),(766.,697.),(781.,700.),(777.,703.),(754.,701.),(740.,700.)],gold),
      line([(754.,693.),(761.,702.)],1.7,rgb(0xb57c4b)),line([(760.,695.),(768.,702.)],1.7,rgb(0xb57c4b)),
      -- Pico largo y bolsa de color ámbar.
      poly(arrayConcat(bez((860.,303.),(909.,306.),(1009.,315.),(1089.,314.)),bez((1089.,314.),(1012.,349.),(965.,386.),(918.,368.)),
         bez((918.,368.),(886.,355.),(871.,330.),(860.,303.))),dark),
      poly(arrayConcat(bez((865.,307.),(923.,311.),(1012.,317.),(1077.,317.)),bez((1077.,317.),(1005.,346.),(963.,379.),(920.,364.)),
         bez((920.,364.),(890.,351.),(875.,329.),(865.,307.))),rgb(0xe6a16a)),
      poly(arrayConcat(bez((875.,315.),(930.,320.),(989.,323.),(1048.,321.)),bez((1048.,321.),(991.,337.),(946.,355.),(920.,348.)),
         bez((920.,348.),(900.,342.),(885.,326.),(875.,315.))),rgb(0xf5cb88)),
      line(bez((887.,324.),(916.,350.),(943.,359.),(970.,351.)),2.5,rgb(0xf8dca0)),
      poly(arrayConcat(bez((864.,279.),(937.,283.),(1025.,301.),(1095.,310.)),bez((1095.,310.),(1110.,312.),(1102.,320.),(1087.,320.)),[(865.,313.)]),dark),
      poly(arrayConcat(bez((866.,283.),(940.,288.),(1025.,305.),(1095.,313.)),[(1095.,316.),(867.,309.)]),gold),
      line(bez((875.,286.),(947.,293.),(1023.,307.),(1080.,312.)),3.,rgb(0xffe4a1)),
      line([(871.,310.),(1088.,317.)],2.0,rgb(0xb77949)),ell(882.,293.,3.2,1.5,0.07,rgb(0x926549)),
      ell(837.,276.,14.,15.,0.,rgb(0xe6bd75)),ell(838.,276.,9.,10.,0.,dark),ell(840.,273.,3.2,3.2,0.,rgb(0xfff4cf)),
      line(bez((822.,259.),(830.,254.),(840.,254.),(847.,260.)),2.8,rgb(0x6b8c87)),
      line(bez((797.,267.),(797.,249.),(806.,241.),(810.,237.)),3.,rgb(0xf8e9bd)),
      line(bez((803.,264.),(805.,244.),(815.,238.),(819.,234.)),3.,rgb(0xf8e9bd)),
      line(bez((810.,260.),(815.,242.),(824.,238.),(826.,235.)),2.7,rgb(0xf8e9bd))
    ] AS pelican,
    arrayConcat(bicycle,pelican) AS rider,
    -- Ondas, estela y salpicaduras donde las ruedas tocan el río.
    arrayConcat(arrayFlatten(arrayMap(cx -> [
       line(bez((cx-103.,879.),(cx-39.,890.),(cx+64.,892.),(cx+120.,878.)),3.,rgb(0x88b5ad)),
       line(bez((cx-128.,891.),(cx-57.,907.),(cx+78.,903.),(cx+145.,890.)),2.,rgb(0x638f91)),
       line(bez((cx-66.,868.),(cx-29.,874.),(cx+34.,875.),(cx+68.,868.)),4.,rgb(0xd9d9b3)),
       line(bez((cx+75.,879.),(cx+83.,867.),(cx+81.,857.),(cx+76.,850.)),3.,rgb(0x9bc2b5)),
       ell(cx+80.,845.,2.6,4.3,-0.4,rgb(0xb7d6c2)),ell(cx+98.,866.,2.1,3.2,0.4,rgb(0xb7d6c2))
    ],[510.,944.])),[
       line(bez((265.,880.),(296.,876.),(342.,877.),(369.,879.)),2.,rgb(0x7faca4)),
       line(bez((275.,898.),(316.,896.),(355.,896.),(399.,898.)),1.7,rgb(0x6a9895)),
       line([(1107.,829.),(1189.,829.)],2.,rgb(0x7caaa2)),line([(1075.,836.),(1117.,836.)],1.5,rgb(0x7caaa2)),
       line([(770.,945.),(863.,945.)],1.8,rgb(0x54858a)),line([(418.,958.),(496.,958.)],1.7,rgb(0x54858a)),
       line([(1098.,940.),(1134.,940.)],1.5,rgb(0xb8ba94)),line([(1208.,679.),(1255.,679.)],2.,rgb(0xc9bd90)),
       line([(1188.,705.),(1269.,705.)],2.,rgb(0xc1b78d)),line([(1255.,774.),(1290.,774.)],2.5,rgb(0xb2b692))
    ]) AS ripples,
    arrayConcat(
      arrayFlatten(arrayMap(ri -> arrayMap(xx -> arrayMap(hh -> [
       line(bez((xx,1007.),(xx-3.,969.),(xx-11.-ri*1.4,1004.-hh),(xx-15.-ri*1.6,984.-hh)),2.4,rgb(0x0c303c)),
       line(bez((xx,1007.),(xx+2.,964.),(xx+13.,976.-hh),(xx+29.,968.-hh)),2.,rgb(0x0c303c)),
       line([(xx-15.-ri*1.6,986.-hh),(xx-18.-ri*1.6,967.-hh)],6.,rgb(0x294c4b))
      ],[42.+33.*(0.5+0.5*sin(ri*2.3))])[1],[22.+ri*15.])[1],range(11))),
      arrayFlatten(arrayMap(ri -> arrayMap(xx -> arrayMap(hh -> [
       line(bez((xx,1008.),(xx+3.,968.),(xx+10.+ri*1.1,1003.-hh),(xx+18.+ri*1.6,978.-hh)),2.7,rgb(0x0c303c)),
       line(bez((xx,1008.),(xx-4.,965.),(xx-18.,993.-hh),(xx-33.,972.-hh)),2.3,rgb(0x0c303c)),
       line([(xx+18.+ri*1.6,981.-hh),(xx+21.+ri*1.6,961.-hh)],6.,rgb(0x495c4d))
      ],[56.+38.*(0.5+0.5*sin(ri*1.8))])[1],[1489.+ri*15.])[1],range(8)))
    ) AS reeds,
    (lp -> paint(lp,forest,paint(lp,banks,if(lp.2<486.,eclipse(lp),water(lp))))) AS landscape,
    -- Reflejo: la misma geometría, invertida y deformada por ondas dentro de SQL.
    (rp -> arrayMap(rbg -> if(rp.2>873.,mix(rbg,
       paint((rp.1+5*sin(rp.2*0.22)+3*sin(rp.2*0.071),1748.-rp.2),rider,rbg),
       0.18*exp(-(rp.2-873.)/135.)*(0.65+0.35*sin(rp.2*0.63))),rbg),[landscape(rp)])[1]) AS reflected,
    (cp -> paint(cp,reeds,paint(cp,ripples,paint(cp,rider,reflected(cp))))) AS scene
SELECT
    clamp(avg(col.1),0.,1.) AS r,
    clamp(avg(col.2),0.,1.) AS g,
    clamp(avg(col.3),0.,1.) AS b,
    pixel % W AS x, intDiv(pixel,W) AS y
FROM (
    SELECT pixel,
      mul(scene(p),1.+(toFloat64(cityHash64(pixel)%1024)/1024.-0.5)*0.018) AS col
    FROM (
      SELECT intDiv(number,{SAMPLES:UInt32}) AS pixel, number%{SAMPLES:UInt32} AS sample,
        (((pixel%W)+if({SAMPLES:UInt32}=1,0.5,(sample+0.5)/{SAMPLES:UInt32}))*dx,
         (intDiv(pixel,W)+if({SAMPLES:UInt32}=1,0.5,modulo((sample+0.5)*0.61803398875,1.0)))*dy) AS p
      FROM numbers_mt(W*H*{SAMPLES:UInt32})
    )
)
GROUP BY pixel
SETTINGS max_threads=8, max_block_size=2048,
    short_circuit_function_evaluation='force_enable', optimize_and_compare_chain=0,
    max_expanded_ast_elements=2000000
FORMAT PNG
