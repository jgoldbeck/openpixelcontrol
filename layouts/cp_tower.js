var striptypes = [
	{ direction: "cw", level: "middle", p0: [0.016, 0.855, 4.143], p1: [-0.82, 0.254, 7.713], pixels: 113 },
	{ direction: "ccw", level: "middle", p0: [0.016, 0.855, 4.143], p1: [0.824, 0.238, 7.702], pixels: 113 },
	{ direction: "cw", level: "top", p0: [0.582, 0.607, 7.788], p1: [0.552, 0.956, 8.961], pixels: 40 },
	{ direction: "ccw", level: "top", p0: [0.607, 0.582, 7.788], p1: [0.956, 0.552, 8.961], pixels: 40 },
];

var center = [0, 0, 0];

var r_step = Math.PI / 6;

var points = [];

function lerp(a, b, s) {
	return a + (b - a) * s;
}

function lerp3(va, vb, s) {
	return [lerp(va[0], vb[0], s), lerp(va[1], vb[1], s), lerp(va[2], vb[2], s)];
}

function rotate(v, r, center) {
	var d = [v[0] - center[0], v[1] - center[1], v[2] - center[2]];
	var s = Math.sin(r);
	var c = Math.cos(r);

	// rotate around z-axis
	var dn = [d[0] * c - d[1] * s, d[0] * s + d[1] * c, d[2]];
	return [dn[0] + center[0], dn[1] + center[1], dn[2] + center[2]];
}

for (var tt = 0; tt < 4; tt++) {
	for (var ii = 0; ii < 12; ii++) {
		var type = striptypes[tt];
		var r = r_step * ii;
		var p0 = rotate(type.p0, r, center);
		var p1 = rotate(type.p1, r, center);

		for (var pp = 0; pp < type.pixels; pp++) {

			var p = lerp3(p0, p1, pp / type.pixels);
			points.push({
				point: p,
				direction: type.direction,
				level: type.level,
				id: ii * tt * pp + 1
			});
		}
	}
}

console.log(JSON.stringify(points, null, '\t'));