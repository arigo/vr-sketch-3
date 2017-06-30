using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class TextHint : WorldObject
{
    public TextMesh textMesh;

    public override void UpdateWorldObject(float[] data)
    {
        int index = 0;
        SetText(GetString(data, ref index));
        Vector3 p1 = GetVec3(data, index);
        Vector3 p2 = GetVec3(data, index + 3);
        transform.localPosition = (p1 + p2) * 0.5f;

        Vector3 p12 = transform.parent.TransformVector(p2 - p1);
        Vector3 pos2head = BaroqueUI.Baroque.GetHeadTransform().position - transform.position;
        Vector3 upwards = Vector3.Cross(pos2head, p12);
        Vector3 forward = Vector3.Cross(upwards, p12);
        if (upwards.y < -1e-3)
            upwards = -upwards;
        transform.rotation = Quaternion.LookRotation(forward, upwards);
    }

    public void SetText(string text)
    {
        textMesh.text = "  " + text + "  ";
        /*
        Bounds bounds = textMesh.GetComponent<Renderer>().bounds;
        Vector3 scale = cube.localScale;
        float s = transform.parent.localScale.y;
        scale.x = bounds.extents.x * 2 / s;
        scale.y = bounds.extents.y * 2.25f / s;
        cube.localScale = scale;
        */
    }
}
