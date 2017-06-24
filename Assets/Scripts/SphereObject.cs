using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class SphereObject : WorldObject
{
    public float localScale;

    public override void UpdateWorldObject(float[] data)
    {
        transform.localPosition = GetVec3(data, 0);

        if (data.Length > 3)
        {
            Color col = GetColor24(data, 3);
            GetComponent<MeshRenderer>().material.color = col;
        }
        if (localScale > 0)
            transform.localScale = Vector3.one * (localScale / transform.parent.lossyScale.y);
    }
}
