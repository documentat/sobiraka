from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase

SOURCE = '''
# A document with horizontal pages

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris sed tortor egestas, feugiat neque eget, venenatis risus. Proin vehicula, tortor vel finibus pulvinar, ante diam lobortis neque, at semper dolor arcu sit amet turpis. Suspendisse dolor lectus, vulputate vitae sollicitudin tempus, congue rhoncus felis. Phasellus placerat augue varius, volutpat nisi nec, luctus urna. Nunc gravida, sem in posuere auctor, urna leo dignissim ex, sit amet tristique quam diam quis nibh. Nullam laoreet placerat molestie. Praesent laoreet urna elementum quam ullamcorper, ac aliquet tellus maximus. Fusce bibendum magna vitae fringilla suscipit. Integer a augue vel augue semper porttitor. Vestibulum ultrices nec arcu ac posuere. Curabitur diam enim, accumsan quis eleifend vitae, commodo at nulla. Curabitur placerat metus at tellus vestibulum, vel dapibus odio porta. Aliquam luctus quam vitae lacus tempus tempor.

Sed in ex hendrerit, lacinia felis convallis, ornare nibh. Donec et luctus dolor. Suspendisse potenti. Proin non libero elit. Aenean et laoreet sapien. Nunc vitae suscipit arcu. Nunc convallis quis odio eget posuere. Sed fringilla, dui et dapibus convallis, arcu dui rhoncus magna, id finibus arcu magna sed magna. Duis nisi turpis, semper a maximus non, interdum nec lacus. Vivamus feugiat nulla id interdum feugiat. Sed sodales viverra fringilla.

Fusce at felis porta, maximus dolor eu, finibus lectus. Quisque faucibus vel dolor nec egestas. Sed sit amet erat sapien. Proin facilisis quam sit amet ante aliquam lacinia. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis eleifend feugiat fringilla. Sed eros nulla, fermentum sed nunc a, aliquam sollicitudin nisl. Sed nec orci euismod, bibendum quam vitae, tristique metus. Etiam eu velit varius eros sodales tempor sit amet vitae nulla. Aenean et leo ultrices leo vehicula elementum. In hac habitasse platea dictumst. Nunc rhoncus fringilla erat ac fermentum. Phasellus eget porta elit.

`<div style="page: landscape; page-break-after: always">`{=html}

In sem justo, vehicula sit amet tortor eu, feugiat iaculis augue. Donec porta felis sem, sit amet dictum lectus volutpat et. Suspendisse malesuada venenatis arcu eget bibendum. Proin libero elit, aliquet in ante eget, scelerisque hendrerit est. Fusce cursus dui tortor, ac convallis turpis vehicula imperdiet. Pellentesque ac urna nulla. Nulla facilisis lacus massa. Etiam ornare velit massa, eget sollicitudin turpis aliquet a. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.

Vestibulum vel lorem vitae felis commodo eleifend. Curabitur ultrices tellus tellus, nec suscipit odio sollicitudin eget. Integer sit amet interdum justo, luctus convallis orci. Vivamus non viverra massa. Donec nibh massa, vestibulum at urna in, fringilla dignissim ex. Etiam luctus blandit molestie. Aliquam semper diam quis libero accumsan pharetra. Fusce efficitur nulla augue, ut faucibus tellus luctus vitae. Nulla luctus consequat sodales. Proin non volutpat odio, ut bibendum nunc. Etiam ultricies feugiat nisi eu euismod. Quisque pretium, sem et congue sodales, nulla mi sollicitudin ipsum, nec porta ipsum risus vel diam. Nulla non velit nec nisi condimentum hendrerit quis sit amet ex.

Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Vivamus lacinia vestibulum sem nec suscipit. Nullam semper orci sed nulla cursus vulputate. Aenean varius, felis at malesuada condimentum, lorem leo feugiat urna, in gravida justo orci non nisl. Praesent vel posuere leo, in tincidunt nisi. Cras at consectetur sapien, sit amet facilisis turpis. In ullamcorper, erat eget consectetur auctor, enim odio fermentum nisi, non venenatis ipsum enim at dolor. Donec id tortor malesuada, dignissim dolor vel, tincidunt elit. Sed molestie, tortor et commodo mattis, magna metus vulputate odio, ac porttitor tortor velit laoreet nulla. Ut semper sem nec efficitur pharetra. Suspendisse vestibulum justo id magna laoreet, ut pharetra ipsum malesuada. Duis quis laoreet eros. Sed eu mattis ipsum. Aliquam ligula neque, blandit quis lacinia malesuada, elementum quis est. Donec ut semper nibh.

Nam ut ultrices diam, ultrices luctus urna. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Proin sollicitudin finibus pulvinar. Nam porta posuere nisi eu blandit. Maecenas eget fermentum velit. Aliquam vehicula leo quis magna dictum condimentum. Nam elit lorem, tincidunt at neque sit amet, tristique placerat odio. Aliquam molestie massa at lectus hendrerit dignissim. Integer urna magna, interdum vitae bibendum non, tincidunt ut lectus.

Mauris at venenatis nulla. Vestibulum nec tortor interdum, fermentum justo ut, ullamcorper est. Nulla sit amet mattis ligula, nec laoreet metus. In nisl est, ultrices convallis venenatis eget, pulvinar ut arcu. Cras nisl augue, porttitor a turpis eu, facilisis pellentesque est. Vestibulum arcu nulla, volutpat vel fringilla nec, pellentesque vel diam. Nulla pellentesque nisl sem, et posuere ante ultricies eu. Vestibulum fringilla molestie ipsum id consequat. Etiam lorem massa, venenatis non elit at, ullamcorper posuere sapien. Maecenas efficitur neque eget rutrum fermentum. Quisque eget dolor dapibus elit tristique bibendum a at dolor.

Curabitur in facilisis metus. Praesent velit neque, tempor id metus eu, laoreet volutpat nisl. Ut justo dolor, ultricies quis fringilla consequat, finibus et velit. Etiam viverra lectus lectus, sit amet semper lectus dignissim at. Cras blandit, enim eu porttitor pharetra, leo magna dictum erat, quis mattis nunc nibh vitae massa. Etiam scelerisque tortor vel arcu imperdiet convallis. In tortor elit, lacinia sit amet nisl vel, sollicitudin consectetur leo. Etiam vel hendrerit diam. Integer rutrum mi non sapien fringilla volutpat. Vestibulum varius tempor lobortis. Nam sit amet tellus vitae massa interdum porta. Maecenas tempor a lorem ultrices venenatis. Maecenas dignissim, felis volutpat tempor commodo, sapien turpis facilisis libero, et auctor ante arcu nec lorem. Nulla mollis pharetra odio sed luctus. Etiam eleifend congue placerat. Quisque purus velit, aliquam quis ligula ut, gravida placerat velit.

`</div>`{=html}

Sed commodo efficitur pharetra. Sed et nibh vitae lectus facilisis volutpat a vitae nibh. Quisque euismod tincidunt nisl, a semper nisi facilisis eget. In hac habitasse platea dictumst. Vestibulum eget posuere risus, id ultrices velit. In tortor felis, vulputate ut arcu at, lobortis vestibulum ex. Etiam risus elit, pharetra id nisi ut, suscipit gravida massa. Duis in auctor enim, eget tincidunt dolor. Fusce a fringilla magna. Quisque maximus lorem in mattis tincidunt. Aenean libero lacus, placerat in lorem eu, lobortis gravida nibh. Phasellus ut faucibus eros. Aenean ac orci velit. Proin auctor, ipsum ac vehicula bibendum, quam purus elementum nisi, vitae blandit arcu ipsum nec nisi. Aenean efficitur viverra ex, id lobortis mauris eleifend eu. Cras finibus justo eget diam venenatis, sed consequat dolor porta.
'''


class TestWeasyPrint_Horizontal(SinglePageProjectTest, WeasyPrintProjectTestCase):
    SOURCE = SOURCE


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
