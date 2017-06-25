using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class CylinderObject : WorldObject
{
    public float y_scale;

    public override void UpdateWorldObject(float[] data)
    {
        Vector3 p1 = GetVec3(data, 0);
        Vector3 p2 = GetVec3(data, 3);
        Color col = GetColor24(data, 6);

        Vector3 scale = transform.localScale;
        scale.y = Vector3.Distance(p1, p2) * y_scale + 0.0025f;
        transform.localScale = scale;
        transform.localPosition = (p1 + p2) * 0.5f;
        if (p1 != p2)
            transform.localRotation = Quaternion.LookRotation(p2 - p1) * Quaternion.LookRotation(Vector3.up);
        
        foreach (var rend in GetComponents<MeshRenderer>())
            rend.material.color = col;
    }
}
